"""Bounded sparse activation for retrieval, separate from truth and inference."""
from __future__ import annotations

import json
import math
from collections import OrderedDict
from ..config import Config
from ..util import canonical_json, sha256_hex
from ..storage.schema import WriterRole


class MemoryManager:
    def __init__(self, db, config=None):
        self.db, self.config = db, config or Config()
        self.cache = OrderedDict()

    def activate(self, seeds):
        c = self.config
        scores = {int(k): float(v) for k, v in seeds.items() if 0 < float(v) <= 1}
        frontier = dict(scores)
        with self.db.read() as r:
            for _ in range(c["activation_depth"]):
                nxt = {}
                for node, score in sorted(frontier.items(), key=lambda x: -x[1])[:c["activation_top_k"]]:
                    edges = r.query("SELECT tgt_id,weight FROM relation_edge WHERE src_id=? AND status='ACTIVE' ORDER BY tgt_id LIMIT ?", (node, c["activation_fan_out_cap"]))
                    for edge in edges:
                        value = score*c["activation_alpha"]*(edge["weight"] if edge["weight"] is not None else 1.0)
                        if value >= c["activation_theta"] and value > scores.get(edge["tgt_id"], 0):
                            scores[edge["tgt_id"]] = value
                            nxt[edge["tgt_id"]] = value
                frontier = nxt
                if not frontier:
                    break
        return sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:c["activation_top_k"]]

    def cache_inference(self, query, dependencies, value):
        key = sha256_hex(canonical_json([query, dependencies]))
        with self.db.write(WriterRole.CACHE) as t:
            t.execute("INSERT OR REPLACE INTO inference_cache VALUES(?,?,?,?)", (key, canonical_json(dependencies), canonical_json(value), self.db.clock.now()))
        self.cache[key] = value
        while len(self.cache) > self.config["workspace_capacity"]:
            self.cache.popitem(last=False)
        return key

    def get_cached(self, query, dependencies):
        key = sha256_hex(canonical_json([query, dependencies]))
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        with self.db.read() as r:
            row = r.one("SELECT body FROM inference_cache WHERE cache_key=?", (key,))
        return json.loads(row[0]) if row else None

    @staticmethod
    def heat(previous, elapsed_days, half_life_days=7):
        if elapsed_days < 0 or half_life_days <= 0:
            raise ValueError("invalid heat interval")
        return previous*math.exp(-math.log(2)*elapsed_days/half_life_days)
