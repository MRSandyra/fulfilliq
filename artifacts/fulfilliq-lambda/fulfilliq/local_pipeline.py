from __future__ import annotations

import json
import shutil
from pathlib import Path

from .config import ensure_dir
from .transform import ContractError, event_type, normalized_jsonl, validate_batch


def ingest_batches(input_dir: Path, output_dir: Path) -> dict:
    """Local equivalent of Lambda: immutable curated objects or whole-batch quarantine."""
    curated = ensure_dir(output_dir / "curated")
    quarantine = ensure_dir(output_dir / "quarantine")
    report = {"processed": 0, "curated": 0, "quarantined": 0, "duplicates": 0, "errors": []}
    for batch_path in sorted(input_dir.glob("*/*.jsonl")):
        report["processed"] += 1
        batch_id = batch_path.stem
        try:
            events = validate_batch(batch_path.read_text(encoding="utf-8"))
            kind = event_type(events)
            destination = ensure_dir(curated / kind) / f"{batch_id}.jsonl"
            content = normalized_jsonl(events)
            if destination.exists():
                if destination.read_bytes() != content:
                    raise ContractError("immutable curated key has mismatched content")
                report["duplicates"] += 1
            else:
                destination.write_bytes(content)
                report["curated"] += 1
        except (OSError, ContractError) as exc:
            report["quarantined"] += 1
            (quarantine / f"{batch_id}.json").write_text(
                json.dumps(
                    {
                        "batch_id": batch_id,
                        "source": str(batch_path),
                        "status": "QUARANTINED",
                        "error": str(exc),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            report["errors"].append({"batch_id": batch_id, "error": str(exc)})
    (output_dir / "ingest_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def reset_output(path: Path) -> None:
    """Used only by callers that explicitly want to rebuild a local target."""
    if path.exists():
        shutil.rmtree(path)
