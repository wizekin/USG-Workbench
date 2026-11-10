"""USBF reference profile 0.1: independently compressed, checksummed blocks.

This experimental profile uses canonical JSON node payloads instead of claiming
the specification's unbenchmarked compact frame layout is production-ready.
Versions, lengths, nesting and decompression limits are enforced before import.
"""
from __future__ import annotations

import binascii
import json
import struct
import uuid
import zlib
from dataclasses import dataclass

from .. import GRAMMAR_VERSION, ONTOLOGY_RELEASE, RULESET_RELEASE
from ..errors import InvariantViolation
from ..util import canonical_json

HEADER = struct.Struct("<4sBBHI16s")
FOOTER = struct.Struct("<QI4s")
BLOCK = struct.Struct("<III")  # compressed length, uncompressed length, crc32
MAX_FILE = 64*1024*1024
MAX_BLOCK = 1024*1024
MAX_RECORDS = 100_000


class DecodeError(InvariantViolation):
    code = "SG-ENC-007"


def varint(n):
    if type(n) is not int or not 0 <= n < 2**64:
        raise ValueError("unsigned 64-bit integer required")
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def read_varint(data, offset=0):
    start, value = offset, 0
    for i in range(10):
        if offset >= len(data):
            raise DecodeError("truncated varint")
        b = data[offset]
        offset += 1
        value |= (b & 127) << (7*i)
        if not b & 128:
            if value >= 2**64 or data[start:offset] != varint(value):
                raise DecodeError("non-canonical varint")
            return value, offset
    raise DecodeError("varint exceeds 64 bits")


def zigzag(n):
    if type(n) is not int or not -(2**63) <= n < 2**63:
        raise ValueError("signed 64-bit integer required")
    return (n << 1) ^ (n >> 63)


def unzigzag(n):
    return (n >> 1) ^ -(n & 1)


def _crc(data):
    return binascii.crc32(data) & 0xffffffff


def _depth(value, at=0):
    if at > 96:
        raise DecodeError("payload nesting exceeds limit")
    if isinstance(value, dict):
        for v in value.values():
            _depth(v, at+1)
    elif isinstance(value, list):
        for v in value:
            _depth(v, at+1)


def _json(data):
    try:
        def pairs(items):
            out = {}
            for k, v in items:
                if k in out:
                    raise DecodeError("duplicate JSON key")
                out[k] = v
            return out
        value = json.loads(data, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(DecodeError("nonfinite number")))
        _depth(value)
        return value
    except (ValueError, UnicodeError, RecursionError, TypeError) as ex:
        raise DecodeError("malformed container JSON") from ex


def encode(records, *, mode="reversible", block_size=64*1024, definitions=None, codec="json", schemas=None):
    if mode not in {"semantic", "reversible"} or not 1024 <= block_size <= MAX_BLOCK:
        raise ValueError("invalid mode or block size")
    if codec not in {'json','compact','template'}:raise ValueError('unknown payload codec')
    blocks, batch, size, count = [], [], 0, 0
    for record in records:
        _depth(record)
        raw = canonical_json(record).encode("utf-8")
        if len(raw) > MAX_BLOCK-2:
            raise ValueError("record exceeds block limit")
        if batch and size+len(raw)+1 > block_size:
            blocks.append(batch)
            batch, size = [], 0
        batch.append(record)
        size += len(raw)+1
        count += 1
        if count > MAX_RECORDS:
            raise ValueError("record count limit")
    if batch:
        blocks.append(batch)
    out = bytearray(HEADER.pack(b"USBF", 0, 3 if codec == "template" else 2 if codec == "compact" else 1, 0, 0, uuid.uuid4().bytes))
    out.extend(varint(0))  # reproducible created timestamp (not an identity)
    directory = []
    for batch in blocks:
        if codec == 'template':
            from .templates import dumps
            raw = dumps(batch, schemas)
        elif codec == 'compact':
            from .compact import dumps
            raw = dumps(batch, schemas)
        else:
            raw = canonical_json(batch).encode("utf-8")
        if len(raw) > MAX_BLOCK:
            raise ValueError("block exceeds limit")
        compressed = zlib.compress(raw, 9)
        offset = len(out)
        out.extend(BLOCK.pack(len(compressed), len(raw), _crc(compressed)))
        out.extend(compressed)
        directory.append({"offset": offset, "length": BLOCK.size+len(compressed), "records": len(batch), "codec": "zlib"})
    start = len(out)
    metadata = {"profile": "USBF-TEMPLATE-0.3" if codec == "template" else "USBF-COMPACT-0.2" if codec == "compact" else "USBF-JSON-0.1", "mode": mode, "grammar_version": GRAMMAR_VERSION,
                "ontology_release": ONTOLOGY_RELEASE, "ruleset_release": RULESET_RELEASE,
                "blocks": directory, "records": count, "definitions": definitions or {}}
    raw_dir = canonical_json(metadata).encode("utf-8")
    out.extend(raw_dir)
    out.extend(FOOTER.pack(start, _crc(raw_dir), b"USBF"))
    if len(out) > MAX_FILE:
        raise ValueError("container exceeds file limit")
    return bytes(out)


class Reader:
    def __init__(self, data):
        self.data = data
        try:
            if len(data) > MAX_FILE or len(data) < HEADER.size+1+FOOTER.size:
                raise DecodeError("file size outside limits")
            magic, major, minor, critical, optional, _ = HEADER.unpack_from(data)
            if magic != b"USBF" or major != 0 or minor not in (1,2,3) or critical or optional:
                raise DecodeError("unsupported USBF version or flags")
            _, end_header = read_varint(data, HEADER.size)
            offset, crc, magic = FOOTER.unpack_from(data, len(data)-FOOTER.size)
            if magic != b"USBF" or not end_header <= offset <= len(data)-FOOTER.size:
                raise DecodeError("bad footer or directory offset")
            raw = data[offset:-FOOTER.size]
            if len(raw) > MAX_BLOCK*8 or _crc(raw) != crc:
                raise DecodeError("directory size/checksum invalid")
            self.metadata = _json(raw)
            m = self.metadata
            if m.get("profile") != {1:'USBF-JSON-0.1',2:'USBF-COMPACT-0.2',3:'USBF-TEMPLATE-0.3'}[minor] or m.get("mode") not in {"semantic", "reversible"}:
                raise DecodeError("unsupported profile or mode")
            if (m["grammar_version"], m["ontology_release"], m["ruleset_release"]) != (GRAMMAR_VERSION, ONTOLOGY_RELEASE, RULESET_RELEASE):
                raise DecodeError("pinned definitions are not installed for this version")
            if type(m["records"]) is not int or not 0 <= m["records"] <= MAX_RECORDS or len(m["blocks"]) > MAX_RECORDS:
                raise DecodeError("record/block count limit")
            cursor, declared = end_header, 0
            total = 0
            for b in m["blocks"]:
                if b["codec"] != "zlib" or type(b["offset"]) is not int or type(b["length"]) is not int or b["offset"] != cursor or not BLOCK.size < b["length"] <= MAX_BLOCK+1024:
                    raise DecodeError("invalid or overlapping block")
                cursor += b["length"]
                if cursor > offset:
                    raise DecodeError("block crosses directory")
                compressed, unpacked, crc = BLOCK.unpack_from(data, b["offset"])
                if compressed != b["length"]-BLOCK.size or not 0 < unpacked <= MAX_BLOCK or type(b["records"]) is not int or not 0 < b["records"] <= MAX_RECORDS:
                    raise DecodeError("block length/count invalid")
                declared += b["records"]
                total += unpacked
            if cursor != offset or declared != m["records"] or total > MAX_FILE:
                raise DecodeError("block totals do not match")
        except (KeyError, TypeError, ValueError, struct.error, IndexError) as ex:
            raise DecodeError("malformed USBF directory") from ex

    def block(self, index):
        try:
            b = self.metadata["blocks"][index]
            compressed_len, unpacked_len, crc = BLOCK.unpack_from(self.data, b["offset"])
            payload = self.data[b["offset"]+BLOCK.size:b["offset"]+b["length"]]
            if _crc(payload) != crc:
                raise DecodeError("block checksum mismatch")
            d = zlib.decompressobj()
            raw = d.decompress(payload, unpacked_len+1)
            if len(raw) != unpacked_len or not d.eof or d.unused_data or d.unconsumed_tail:
                raise DecodeError("decompressed length or trailing data invalid")
            if self.metadata['profile'] == 'USBF-TEMPLATE-0.3':
                from .templates import loads
                records = loads(raw)
            elif self.metadata['profile'] == 'USBF-COMPACT-0.2':
                from .compact import loads
                records = loads(raw)
            else:
                records = _json(raw)
            if not isinstance(records, list) or len(records) != b["records"]:
                raise DecodeError("block record count mismatch")
            return records
        except (IndexError, TypeError, KeyError, zlib.error) as ex:
            raise DecodeError("malformed USBF block") from ex

    def records(self):
        for i in range(len(self.metadata["blocks"])):
            yield from self.block(i)


def decode(data):
    return list(Reader(data).records())
