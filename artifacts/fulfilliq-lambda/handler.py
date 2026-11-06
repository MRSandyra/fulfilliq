"""AWS Lambda adapter; core validation remains in `fulfilliq.transform`."""
from __future__ import annotations

import json
import logging
import os
from time import perf_counter
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

from fulfilliq.transform import ContractError, event_type, normalized_jsonl, validate_batch

LOG = logging.getLogger()
LOG.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def _destination_prefixes(key: str) -> tuple[str, str, str]:
    """Map a raw key to its expected event type and isolated output prefixes."""
    parts = key.split("/")
    if len(parts) == 3 and parts[0] == "raw":
        expected_kind = parts[1]
        if expected_kind not in {"order_placed", "delivery_outcome"}:
            raise ContractError("unsupported raw event prefix")
        return expected_kind, f"curated/{expected_kind}", "quarantine"
    if len(parts) == 5 and parts[0:2] == ["raw", "olist"]:
        run_id, expected_kind = parts[2], parts[3]
        if not run_id or expected_kind not in {"order_placed", "delivery_outcome"}:
            raise ContractError("unsupported Olist replay raw prefix")
        return (
            expected_kind,
            f"curated/olist/{run_id}/{expected_kind}",
            f"quarantine/olist/{run_id}",
        )
    raise ContractError("raw key must be a smoke or namespaced Olist replay key")


def _put_immutable(client, *, bucket: str, key: str, body: bytes, content_type: str) -> bool:
    """Write once, or prove an at-least-once delivery is the same batch.

    Returns ``True`` when an identical curated object already existed.  A raw
    object manually overwritten under the same content-hash filename is sent to
    quarantine instead of replacing trusted curated evidence.
    """
    try:
        existing = client.get_object(Bucket=bucket, Key=key)["Body"].read()
    except KeyError:  # Lightweight local test doubles.
        existing = None
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"NoSuchKey", "404", "NotFound"}:
            raise
        existing = None
    if existing is not None:
        if existing != body:
            raise ContractError("immutable curated key has mismatched content")
        return True
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ServerSideEncryption="AES256",
        ContentType=content_type,
    )
    return False


def handler(event: dict, context, *, s3_client=None) -> dict:
    client = s3_client or boto3.client("s3")
    configured_bucket = os.environ.get("FULFILLIQ_BUCKET")
    results = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        if configured_bucket and bucket != configured_bucket:
            raise PermissionError("unexpected bucket")
        if not key.startswith("raw/") or not key.endswith(".jsonl"):
            LOG.info(json.dumps({"status": "ignored", "key": key}))
            continue
        started = perf_counter()
        batch_id = key.rsplit("/", 1)[-1].removesuffix(".jsonl")
        quarantine_prefix = "quarantine"
        try:
            expected_kind, curated_prefix, quarantine_prefix = _destination_prefixes(key)
            body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
            events = validate_batch(body.decode("utf-8"))
            kind = event_type(events)
            if kind != expected_kind:
                raise ContractError("event_type does not match the raw key prefix")
            curated_key = f"{curated_prefix}/{batch_id}.jsonl"
            duplicate = _put_immutable(
                client,
                bucket=bucket,
                key=curated_key,
                body=normalized_jsonl(events),
                content_type="application/x-ndjson",
            )
            payload = {"status": "duplicate" if duplicate else "curated", "batch_id": batch_id, "event_type": kind, "count": len(events), "elapsed_ms": round((perf_counter() - started) * 1000, 2)}
            LOG.info(json.dumps(payload))
            results.append(payload)
        except (UnicodeDecodeError, ContractError, OSError, ValueError) as exc:
            quarantine_key = f"{quarantine_prefix}/{batch_id}.json"
            report = {"status": "quarantined", "batch_id": batch_id, "error": str(exc)[:500]}
            client.put_object(Bucket=bucket, Key=quarantine_key, Body=json.dumps(report).encode("utf-8"), ServerSideEncryption="AES256", ContentType="application/json")
            LOG.error(json.dumps(report))
            results.append(report)
    return {"records": results}
