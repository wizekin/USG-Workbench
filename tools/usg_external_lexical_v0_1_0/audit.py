"""Offline reconciliation for the external lexical crawl's durable state."""
from __future__ import annotations

import re


_COUNTERS = (
    "processed_headwords", "processed_entries", "processed_senses",
    "failed_headwords", "failed_pages", "retried_headwords",
    "recovered_headwords", "retry_failed_headwords",
    "retry_dead_letter_headwords", "stored_bytes",
)


def audit_crawl_state(checkpoint: dict, manifest: dict, shard_inventory: list[dict]) -> dict:
    """Compare checkpoint, manifest and physical shard metadata without mutating data."""
    errors: list[str] = []
    warnings: list[str] = []
    inventory = [item for item in shard_inventory if item.get("type", "file") == "file"
                 and str(item.get("path", item.get("name", ""))).endswith(".jsonl.gz")]
    paths = [str(item.get("path", item.get("name", ""))) for item in inventory]
    if len(paths) != len(set(paths)):
        errors.append("shard inventory contains duplicate paths")

    for key in _COUNTERS:
        if int(checkpoint.get(key, 0)) != int(manifest.get(key, 0)):
            errors.append(f"checkpoint/manifest mismatch: {key}")

    checkpoint_batch = int(checkpoint.get("batch_number", 0))
    manifest_batch = int(manifest.get("batch_count", 0))
    if checkpoint_batch != manifest_batch:
        errors.append("checkpoint/manifest mismatch: batch_number/batch_count")

    physical_bytes = sum(int(item.get("size", 0)) for item in inventory)
    if physical_bytes != int(manifest.get("stored_bytes", 0)):
        errors.append(
            f"physical shard bytes ({physical_bytes}) do not match manifest stored_bytes "
            f"({manifest.get('stored_bytes', 0)})"
        )

    retry_queue = checkpoint.get("retry_queue", [])
    if int(manifest.get("pending_retries", 0)) != len(retry_queue):
        errors.append("checkpoint retry_queue length does not match manifest pending_retries")
    if int(checkpoint.get("recovered_headwords", 0)) > int(checkpoint.get("retried_headwords", 0)):
        errors.append("recovered_headwords exceeds retried_headwords")
    if int(checkpoint.get("retry_failed_headwords", 0)) > int(checkpoint.get("retried_headwords", 0)):
        errors.append("retry_failed_headwords exceeds retried_headwords")

    batch_numbers: dict[int, list[dict]] = {}
    pattern = re.compile(r"/batch-(\d{6})-[^/]+\.jsonl\.gz$")
    for item in inventory:
        path = str(item.get("path", item.get("name", "")))
        match = pattern.search("/" + path.lstrip("/"))
        if not match:
            warnings.append(f"unrecognized shard filename: {path}")
            continue
        number = int(match.group(1))
        batch_numbers.setdefault(number, []).append(item)
        if number > checkpoint_batch:
            errors.append(f"shard batch {number:06d} is ahead of checkpoint batch {checkpoint_batch:06d}")

    duplicate_batches = []
    for number, items in sorted(batch_numbers.items()):
        if len(items) > 1:
            shas = {item.get("sha") or item.get("sha256") for item in items}
            duplicate_batches.append({
                "batch_number": number,
                "paths": [str(item.get("path", item.get("name", ""))) for item in items],
                "identical_blob": len(shas) == 1 and None not in shas,
            })
            if len(shas) > 1:
                errors.append(f"batch number {number:06d} maps to different shard contents")
            else:
                warnings.append(f"duplicate physical shard copies for batch {number:06d}")

    last_batch = manifest.get("last_batch") or {}
    last_path = last_batch.get("path")
    if last_path and last_path not in paths:
        errors.append("manifest last_batch path is absent from shard inventory")
    elif last_path:
        last_item = next(item for item in inventory
                         if str(item.get("path", item.get("name", ""))) == last_path)
        if int(last_item.get("size", 0)) != int(last_batch.get("bytes", 0)):
            errors.append("manifest last_batch byte count does not match shard inventory")

    return {
        "audit_version": "usg-external-lexical-state-audit/0.1.0",
        "status": "failed" if errors else ("passed_with_warnings" if warnings else "passed"),
        "checks": {
            "shard_file_count": len(inventory),
            "physical_stored_bytes": physical_bytes,
            "checkpoint_batch_number": checkpoint_batch,
            "manifest_batch_count": manifest_batch,
            "retry_queue_length": len(retry_queue),
            "duplicate_batches": duplicate_batches,
        },
        "errors": errors,
        "warnings": warnings,
        "mutated_data": False,
        "limitations": [
            "This audit reconciles metadata and Git blob inventory; it does not decompress or linguistically validate shard records.",
            "Duplicate identical blobs are reported as warnings because historical runs may have published duplicate copies; their bytes remain included in physical storage accounting.",
        ],
    }
