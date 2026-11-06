from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from .config import ensure_dir

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
        "orphan_outcomes": int(
            con.execute(
                "SELECT count(*) FROM outcomes o LEFT JOIN placed p USING(order_id) WHERE p.order_id IS NULL"
            ).fetchone()[0]
        ),
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
        (output_dir / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")
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
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    con.close()
    return manifest


def copy_dashboard_data(input_dir: Path, output_dir: Path, *, mode: str) -> None:
    ensure_dir(output_dir)
    for path in input_dir.glob("*.json"):
        (output_dir / path.name).write_bytes(path.read_bytes())
    manifest = json.loads((output_dir / "manifest.json").read_text())
    manifest["dataset_mode"] = mode
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
