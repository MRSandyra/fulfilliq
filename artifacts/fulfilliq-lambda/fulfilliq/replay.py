from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import DEFAULT_MAX_BYTES, DEFAULT_MAX_RECORDS, ensure_dir
from .transform import batch_id_from_bytes, canonical_json


def _load_events(path: Path, as_of: datetime | None) -> list[dict]:
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if as_of and datetime.fromisoformat(event["event_ts"]) > as_of:
            continue
        events.append(event)
    return sorted(events, key=lambda e: (e["event_ts"], e["order_id"]))


def create_batches(
    input_dir: Path,
    output_dir: Path,
    *,
    as_of: str | None = None,
    max_records: int = DEFAULT_MAX_RECORDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    order_limit: int | None = None,
) -> dict:
    if order_limit is not None and order_limit < 1:
        raise ValueError("order_limit must be at least 1")
    cutoff = datetime.fromisoformat(as_of) if as_of else None
    if order_limit is not None and any(output_dir.glob("*/*.jsonl")):
        raise ValueError("staged replay output must be a new, empty directory")

    placements = _load_events(input_dir / "order_placed.jsonl", cutoff)
    if order_limit is not None:
        placements = placements[:order_limit]
        selected_order_ids = {event["order_id"] for event in placements}
        outcomes = [
            event
            for event in _load_events(input_dir / "delivery_outcome.jsonl", cutoff)
            if event["order_id"] in selected_order_ids
        ]
    else:
        outcomes = _load_events(input_dir / "delivery_outcome.jsonl", cutoff)

    result: dict[str, list[str]] = {}
    event_sets = {"order_placed": placements, "delivery_outcome": outcomes}
    for kind, events in event_sets.items():
        target = ensure_dir(output_dir / kind)
        current: list[str] = []
        ids: list[str] = []
        for event in events:
            row = canonical_json(event)
            candidate = current + [row]
            candidate_bytes = ("\n".join(candidate) + "\n").encode("utf-8")
            if current and (len(candidate) > max_records or len(candidate_bytes) > max_bytes):
                content = ("\n".join(current) + "\n").encode("utf-8")
                batch_id = batch_id_from_bytes(content)
                (target / f"{batch_id}.jsonl").write_bytes(content)
                ids.append(batch_id)
                current = [row]
            else:
                current = candidate
        if current:
            content = ("\n".join(current) + "\n").encode("utf-8")
            batch_id = batch_id_from_bytes(content)
            (target / f"{batch_id}.jsonl").write_bytes(content)
            ids.append(batch_id)
        result[kind] = ids
    manifest = {"as_of": as_of, "batches": result}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if order_limit is not None:
        (output_dir / "stage-manifest.json").write_text(
            json.dumps(
                {
                    "as_of": as_of,
                    "order_limit": order_limit,
                    "selected_orders": len(placements),
                    "event_counts": {kind: len(events) for kind, events in event_sets.items()},
                    "batches": result,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return result
