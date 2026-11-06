from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from pydantic import ValidationError

from .config import MAX_BATCH_BYTES, MAX_RECORDS_PER_BATCH
from .contracts import ContractError, parse_event


def canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def batch_id_from_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def validate_batch(text: str, *, max_bytes: int = MAX_BATCH_BYTES) -> list[dict]:
    encoded = text.encode("utf-8")
    if len(encoded) > max_bytes:
        raise ContractError(f"batch exceeds {max_bytes} bytes")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ContractError("batch has no JSONL records")
    if len(lines) > MAX_RECORDS_PER_BATCH:
        raise ContractError(f"batch exceeds {MAX_RECORDS_PER_BATCH} records")
    parsed: list[dict] = []
    ids: set[str] = set()
    kinds: set[str] = set()
    for number, line in enumerate(lines, 1):
        try:
            candidate = json.loads(line)
            event = parse_event(candidate)
        except (json.JSONDecodeError, ValidationError, ContractError, ValueError) as exc:
            raise ContractError(f"line {number}: {exc}") from exc
        if event.order_id in ids:
            raise ContractError(f"line {number}: duplicate order_id within batch")
        ids.add(event.order_id)
        kinds.add(event.event_type)
        parsed.append(event.model_dump(mode="json"))
    if len(kinds) != 1:
        raise ContractError("a batch must contain one event_type")
    return parsed


def normalize_event(event: dict) -> dict:
    parsed = parse_event(event)
    value = parsed.model_dump(mode="json")
    for key in ("customer_state", "seller_state"):
        if value.get(key):
            value[key] = value[key].upper()
    if value.get("product_category_primary") is None:
        value["product_category_primary"] = "UNKNOWN"
    return value


def normalized_jsonl(events: Iterable[dict]) -> bytes:
    rows = [canonical_json(normalize_event(event)) for event in events]
    return ("\n".join(rows) + "\n").encode("utf-8")


def event_type(events: list[dict]) -> str:
    if not events:
        raise ContractError("empty event list")
    return str(events[0]["event_type"])
