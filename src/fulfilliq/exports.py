from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from numbers import Real
from pathlib import Path

import duckdb

from .config import ensure_dir

# This is an allowlist, not a best-effort redaction pass.  A dashboard export is
# a public boundary: adding a new analytics JSON file must be reviewed before it
# can be served by Vite.
DASHBOARD_PUBLIC_FILES = frozenset(
    {
        "manifest.json",
        "overview.json",
        "sla_daily.json",
        "sla_regions.json",
        "sla_categories.json",
        "quality.json",
        "risk_summary.json",
    }
)
FORBIDDEN_DASHBOARD_FIELDS = frozenset(
    {
        "order_id",
        "customer_id",
        "customer_unique_id",
        "seller_id",
        "product_id",
        "email",
        "phone",
        "address",
        "zip_code",
        "postal_code",
        "raw_score",
        "delivered_date",
    }
)
PII_FIELD_TOKENS = frozenset(
    {
        "email",
        "phone",
        "address",
        "street",
        "postal",
        "zip",
        "latitude",
        "longitude",
    }
)

LOCAL_SQL = """
CREATE OR REPLACE VIEW placed AS
SELECT * EXCLUDE (rn) FROM (
  SELECT *, row_number() OVER (PARTITION BY order_id ORDER BY event_ts, filename) AS rn
  FROM read_json_auto('{placed}', filename=true)
) WHERE rn = 1;
CREATE OR REPLACE VIEW outcomes AS
SELECT * EXCLUDE (rn) FROM (
  SELECT *, row_number() OVER (PARTITION BY order_id ORDER BY event_ts, filename) AS rn
  FROM read_json_auto('{outcomes}', filename=true)
) WHERE rn = 1;
CREATE OR REPLACE VIEW facts AS
SELECT p.*, o.delivered_date, o.final_order_status,
 CASE WHEN o.final_order_status = 'delivered' AND o.delivered_date IS NOT NULL
      AND p.promised_delivery_date IS NOT NULL THEN 1 ELSE 0 END AS eligible_delivery,
 CASE WHEN o.final_order_status = 'delivered' AND CAST(o.delivered_date AS DATE) > CAST(p.promised_delivery_date AS DATE)
      THEN 1 ELSE 0 END AS delivery_late
FROM placed p LEFT JOIN outcomes o USING(order_id);
"""


def _json_safe(value: object) -> object:
    """Convert dataframe NaN/Infinity values to JSON's explicit null."""
    if isinstance(value, Real) and not isinstance(value, bool):
        return None if not math.isfinite(float(value)) else value
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(_json_safe(value), indent=2, default=str, allow_nan=False), encoding="utf-8"
    )


def _glob(path: Path) -> str:
    return str(path / "curated" / "*" / "*.jsonl").replace("\\", "/")


def export_local(input_dir: Path, output_dir: Path, *, mode: str = "local") -> dict:
    ensure_dir(output_dir)
    placed = str(input_dir / "curated" / "order_placed" / "*.jsonl").replace("\\", "/")
    outcomes = str(input_dir / "curated" / "delivery_outcome" / "*.jsonl").replace("\\", "/")
    if not list((input_dir / "curated" / "order_placed").glob("*.jsonl")):
        raise ValueError("no curated order_placed batches found")
    con = duckdb.connect()
    con.execute(LOCAL_SQL.format(placed=placed, outcomes=outcomes))
    overview = (
        con.execute("""SELECT count(*) total_orders, sum(eligible_delivery) eligible_delivered_orders,
      sum(delivery_late) late_delivered_orders,
      CASE WHEN sum(eligible_delivery)=0 THEN NULL ELSE sum(delivery_late)::DOUBLE/sum(eligible_delivery) END late_delivery_rate,
      round(sum(order_value_brl),2) gmv_brl,
      count(*)-sum(eligible_delivery) undelivered_orders
      FROM facts""")
        .fetchdf()
        .iloc[0]
        .to_dict()
    )
    daily = (
        con.execute("""SELECT substr(event_ts,1,10) purchase_date, count(*) orders_placed,
      sum(eligible_delivery) eligible_delivered_orders, sum(delivery_late) late_delivered_orders,
      CASE WHEN sum(eligible_delivery)=0 THEN NULL ELSE sum(delivery_late)::DOUBLE/sum(eligible_delivery) END late_delivery_rate,
      round(sum(order_value_brl),2) gmv_brl FROM facts GROUP BY 1 ORDER BY 1""")
        .fetchdf()
        .to_dict("records")
    )
    regions = (
        con.execute("""SELECT coalesce(customer_state,'UNKNOWN') customer_state, count(*) orders_placed,
      sum(eligible_delivery) eligible_delivered_orders, sum(delivery_late) late_delivered_orders,
      CASE WHEN sum(eligible_delivery)=0 THEN NULL ELSE sum(delivery_late)::DOUBLE/sum(eligible_delivery) END late_delivery_rate
      FROM facts GROUP BY 1 ORDER BY late_delivery_rate DESC NULLS LAST, customer_state""")
        .fetchdf()
        .to_dict("records")
    )
    categories = (
        con.execute("""SELECT coalesce(product_category_primary,'UNKNOWN') product_category_primary, count(*) orders_placed,
      sum(eligible_delivery) eligible_delivered_orders, sum(delivery_late) late_delivered_orders,
      CASE WHEN sum(eligible_delivery)=0 THEN NULL ELSE sum(delivery_late)::DOUBLE/sum(eligible_delivery) END late_delivery_rate
      FROM facts GROUP BY 1 ORDER BY late_delivery_rate DESC NULLS LAST, product_category_primary LIMIT 30""")
        .fetchdf()
        .to_dict("records")
    )
    ing = input_dir / "ingest_report.json"
    ingest = json.loads(ing.read_text()) if ing.exists() else {}
    quality = {
        "label_coverage": overview["eligible_delivered_orders"] / overview["total_orders"]
        if overview["total_orders"]
        else None,
        "quarantined_batches": ingest.get("quarantined", 0),
        "duplicate_batches": ingest.get("duplicates", 0),
        "orphan_outcomes": _orphan_outcomes(con),
        "definition": "Late means delivered calendar date is after promised calendar date.",
    }
    risk = {
        "model_available": False,
        "message": "No measured local model run has been attached to this export.",
    }
    payloads = {
        "overview.json": overview,
        "sla_daily.json": daily,
        "sla_regions.json": regions,
        "sla_categories.json": categories,
        "quality.json": quality,
        "risk_summary.json": risk,
    }
    for name, value in payloads.items():
        _write_json(output_dir / name, value)
    manifest = {
        "schema_version": 1,
        "dataset_mode": mode,
        "source_name": "Synthetic FulfillIQ fixtures"
        if mode == "synthetic"
        else "Olist Brazilian E-Commerce Public Dataset",
        "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "source_period": "2016-2018" if mode != "synthetic" else "synthetic",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_system": "duckdb-local",
        "model_version": None,
        "files": list(payloads),
    }
    _write_json(output_dir / "manifest.json", manifest)
    con.close()
    return manifest


def _orphan_outcomes(con: duckdb.DuckDBPyConnection) -> int:
    row = con.execute(
        "SELECT count(*) FROM outcomes o LEFT JOIN placed p USING(order_id) WHERE p.order_id IS NULL"
    ).fetchone()
    if row is None:
        raise RuntimeError("orphan outcome query returned no row")
    return int(row[0])


def copy_dashboard_data(input_dir: Path, output_dir: Path, *, mode: str) -> None:
    """Publish only reviewed aggregate artifacts to the browser directory.

    The source directory can contain local-only analysis files.  Unknown JSON
    files and identifier-like fields are rejected rather than silently copied.
    """
    ensure_dir(output_dir)
    paths = {path.name: path for path in input_dir.glob("*.json")}
    required = DASHBOARD_PUBLIC_FILES
    missing = required - paths.keys()
    if missing:
        raise ValueError(f"dashboard export is missing required files: {sorted(missing)}")
    unknown = paths.keys() - DASHBOARD_PUBLIC_FILES
    if unknown:
        raise ValueError(f"dashboard export contains unreviewed JSON files: {sorted(unknown)}")
    stale = {path.name for path in output_dir.glob("*.json")} - DASHBOARD_PUBLIC_FILES
    if stale:
        raise ValueError(f"dashboard output contains stale unreviewed JSON files: {sorted(stale)}")
    for name, path in paths.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        _assert_dashboard_safe(payload, source=name)
        (output_dir / name).write_bytes(path.read_bytes())
    manifest = json.loads((output_dir / "manifest.json").read_text())
    manifest["dataset_mode"] = mode
    _write_json(output_dir / "manifest.json", manifest)


def _assert_dashboard_safe(value: object, *, source: str, path: str = "$") -> None:
    """Reject fields that can identify people, orders, or individual outcomes."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if _is_forbidden_dashboard_field(normalized):
                raise ValueError(f"dashboard privacy boundary rejected {source}:{path}.{key}")
            _assert_dashboard_safe(child, source=source, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_dashboard_safe(child, source=source, path=f"{path}[{index}]")


def _is_forbidden_dashboard_field(field: str) -> bool:
    tokens = set(field.split("_"))
    return (
        field in FORBIDDEN_DASHBOARD_FIELDS
        or field == "id"
        or field.endswith("_id")
        or (field.endswith("_name") and field != "source_name")
        or bool(tokens & PII_FIELD_TOKENS)
    )
