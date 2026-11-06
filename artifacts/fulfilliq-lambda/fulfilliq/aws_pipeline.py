from __future__ import annotations

import os
import re
from pathlib import Path

import boto3

EVENT_UPLOAD_ORDER = ("order_placed", "delivery_outcome")
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def planned_uploads(
    source: Path, *, limit_batches: int, run_id: str | None = None
) -> list[tuple[Path, str]]:
    """Return an ordered, deterministic upload manifest without writing to AWS.

    Placements are always uploaded before outcomes.  A namespaced ``run_id`` is
    required for an Olist replay so its curated data can be queried separately
    from the synthetic smoke-test prefix.
    """
    if limit_batches < 1:
        raise ValueError("limit_batches must be at least 1")
    if run_id is not None and not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must be 1-64 lowercase letters, digits, or hyphens")

    uploads: list[tuple[Path, str]] = []
    for kind in EVENT_UPLOAD_ORDER:
        for path in sorted((source / kind).glob("*.jsonl")):
            prefix = f"raw/olist/{run_id}/{kind}" if run_id else f"raw/{kind}"
            uploads.append((path, f"{prefix}/{path.name}"))
    return uploads[:limit_batches]


def upload_events(
    source: Path, *, mode: str, limit_batches: int = 5, run_id: str | None = None
) -> list[str]:
    if mode not in {"dry-run", "apply"}:
        raise ValueError("mode must be dry-run or apply")
    uploads = planned_uploads(source, limit_batches=limit_batches, run_id=run_id)
    files = [path for path, _ in uploads]
    keys = [key for _, key in uploads]
    if mode == "dry-run":
        return keys
    if os.getenv("ALLOW_CLOUD_DEPLOY") != "true":
        raise PermissionError(
            "cloud upload blocked: set temporary ALLOW_CLOUD_DEPLOY=true after owner approval"
        )
    bucket = os.getenv("FULFILLIQ_BUCKET")
    if not bucket:
        raise ValueError("FULFILLIQ_BUCKET is required for apply mode")
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
    client = boto3.client("s3", region_name=region)
    for path, key in zip(files, keys, strict=True):
        client.upload_file(str(path), bucket, key)
    return keys
