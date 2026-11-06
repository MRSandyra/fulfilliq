from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd

from .features import feature_frame


def score_aggregate(model_dir: Path, prepared_dir: Path, output: Path) -> dict:
    """Write a public-safe score summary without IDs or eventual outcomes."""
    model = joblib.load(model_dir / "model.joblib")
    report = json.loads((model_dir / "metrics.json").read_text(encoding="utf-8"))
    facts = pd.read_json(prepared_dir / "facts.jsonl", lines=True)
    X, _, _ = feature_frame(facts)
    probabilities = model.predict_proba(X)[:, 1]
    bins = pd.cut(
        probabilities, bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], include_lowest=True
    )
    summary = (
        pd.DataFrame({"risk_bin": bins, "probability": probabilities})
        .groupby("risk_bin", observed=False)
        .agg(orders=("probability", "size"), mean_predicted_risk=("probability", "mean"))
        .reset_index()
    )
    payload = {
        "model_available": True,
        "model_version": report["model_version"],
        "scored_at_utc": datetime.now(UTC).isoformat(),
        "metrics": report["metrics"],
        "risk_bins": [
            {
                "risk_bin": str(row.risk_bin),
                "orders": int(row.orders),
                "mean_predicted_risk": float(row.mean_predicted_risk),
            }
            for row in summary.itertuples()
        ],
        "notice": "Aggregated historical scores only; no raw order IDs or eventual outcomes are exported.",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "risk_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
