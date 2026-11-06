from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .config import SOURCE_FILES, ensure_dir

REQUIRED_COLUMNS = {
    "orders": {
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    },
    "items": {"order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"},
    "customers": {"customer_id", "customer_state"},
    "products": {"product_id", "product_category_name"},
    "sellers": {"seller_id", "seller_state"},
}


class SourceValidationError(ValueError):
    pass


def source_manifest(source: Path) -> dict:
    files = []
    for logical, filename in SOURCE_FILES.items():
        path = source / filename
        if path.exists():
            files.append(
                {
                    "logical_name": logical,
                    "name": filename,
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return {"generated_at_utc": datetime.now(UTC).isoformat(), "files": files}


def read_source(source: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for logical, filename in SOURCE_FILES.items():
        path = source / filename
        if logical == "translations" and not path.exists():
            continue
        if not path.exists():
            raise SourceValidationError(f"missing required source file: {filename}")
        frames[logical] = pd.read_csv(path)
        missing = REQUIRED_COLUMNS.get(logical, set()) - set(frames[logical].columns)
        if missing:
            raise SourceValidationError(f"{filename} missing required columns: {sorted(missing)}")
    if frames["orders"]["order_id"].duplicated().any():
        raise SourceValidationError("orders source has duplicate order_id values")
    return frames


def validate_source(source: Path) -> dict:
    frames = read_source(source)
    orders, items, customers = frames["orders"], frames["items"], frames["customers"]
    report = source_manifest(source)
    report["row_counts"] = {name: int(len(frame)) for name, frame in frames.items()}
    report["null_counts"] = {
        "orders_delivered_date": int(orders["order_delivered_customer_date"].isna().sum()),
        "orders_estimated_date": int(orders["order_estimated_delivery_date"].isna().sum()),
        "customer_state": int(customers["customer_state"].isna().sum()),
    }
    report["referential_integrity"] = {
        "items_without_order": int((~items["order_id"].isin(orders["order_id"])).sum()),
        "orders_without_customer": int(
            (~orders["customer_id"].isin(customers["customer_id"])).sum()
        ),
    }
    return report


def _order_facts(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = frames["orders"].copy()
    items = frames["items"].copy()
    products = frames["products"].copy()
    sellers = frames["sellers"].copy()
    customers = frames["customers"][["customer_id", "customer_state"]].copy()
    if (pd.to_numeric(items["freight_value"], errors="coerce") < 0).any():
        raise SourceValidationError("order items contain negative freight_value")
    items["price"] = pd.to_numeric(items["price"], errors="raise")
    items["freight_value"] = pd.to_numeric(items["freight_value"], errors="raise")
    rich = items.merge(
        products[["product_id", "product_category_name"]], on="product_id", how="left"
    )
    rich = rich.merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left")
    if "translations" in frames:
        rich = rich.merge(frames["translations"], on="product_category_name", how="left")
    else:
        rich["product_category_name_english"] = None
    rich["category"] = (
        rich["product_category_name_english"]
        .fillna(rich["product_category_name"])
        .fillna("UNKNOWN")
    )
    ranked = rich.sort_values(
        ["order_id", "price", "order_item_id", "product_id"], ascending=[True, False, True, True]
    )
    primary = ranked.drop_duplicates("order_id")[["order_id", "category"]].rename(
        columns={"category": "product_category_primary"}
    )
    aggregates = rich.groupby("order_id", as_index=False).agg(
        items_count=("order_item_id", "count"),
        seller_count=("seller_id", "nunique"),
        order_value_brl=("price", "sum"),
        freight_brl=("freight_value", "sum"),
    )
    state_counts = rich.groupby("order_id")["seller_state"].nunique().rename("seller_state_count")
    first_seller = rich.sort_values(["order_id", "seller_id"]).drop_duplicates("order_id")[
        ["order_id", "seller_state"]
    ]
    aggregates = (
        aggregates.merge(state_counts, on="order_id")
        .merge(first_seller, on="order_id")
        .merge(primary, on="order_id")
    )
    aggregates["seller_state"] = aggregates.apply(
        lambda row: "MULTI" if row.seller_count > 1 else row.seller_state, axis=1
    )
    facts = orders.merge(customers, on="customer_id", how="left").merge(
        aggregates.drop(columns="seller_state_count"), on="order_id", how="left"
    )
    if facts["order_id"].duplicated().any():
        raise AssertionError("one-order-grain invariant violated")
    return facts


def prepare(source: Path, output: Path) -> dict:
    frames = read_source(source)
    facts = _order_facts(frames)
    ensure_dir(output)
    placed = facts[
        [
            "order_id",
            "order_purchase_timestamp",
            "order_estimated_delivery_date",
            "customer_state",
            "seller_state",
            "items_count",
            "seller_count",
            "order_value_brl",
            "freight_brl",
            "product_category_primary",
        ]
    ].dropna(subset=["order_purchase_timestamp", "order_estimated_delivery_date", "items_count"])
    placed_events = []
    for row in placed.to_dict("records"):
        placed_events.append(
            {
                "schema_version": 1,
                "event_type": "order_placed",
                "order_id": row["order_id"],
                "event_ts": str(row["order_purchase_timestamp"]),
                "promised_delivery_date": str(row["order_estimated_delivery_date"])[:10],
                "customer_state": row["customer_state"]
                if pd.notna(row["customer_state"])
                else None,
                "seller_state": row["seller_state"] if pd.notna(row["seller_state"]) else None,
                "items_count": int(row["items_count"]),
                "seller_count": int(row["seller_count"]),
                "order_value_brl": round(float(row["order_value_brl"]), 2),
                "freight_brl": round(float(row["freight_brl"]), 2),
                "product_category_primary": row["product_category_primary"]
                if pd.notna(row["product_category_primary"])
                else "UNKNOWN",
            }
        )
    outcomes = facts[
        (facts["order_status"] == "delivered")
        & facts["order_delivered_customer_date"].notna()
        & facts["order_estimated_delivery_date"].notna()
    ]
    outcome_events = [
        {
            "schema_version": 1,
            "event_type": "delivery_outcome",
            "order_id": row["order_id"],
            "event_ts": str(row["order_delivered_customer_date"]),
            "delivered_date": str(row["order_delivered_customer_date"])[:10],
            "promised_delivery_date": str(row["order_estimated_delivery_date"])[:10],
            "final_order_status": "delivered",
        }
        for row in outcomes.to_dict("records")
    ]
    for name, events in (("order_placed", placed_events), ("delivery_outcome", outcome_events)):
        (output / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(x, sort_keys=True) for x in events) + ("\n" if events else ""),
            encoding="utf-8",
        )
    quality = {
        "source_status_counts": {
            str(k): int(v) for k, v in facts["order_status"].value_counts(dropna=False).items()
        },
        "placed_events": len(placed_events),
        "outcome_events": len(outcome_events),
        "missing_customer_state": int(facts["customer_state"].isna().sum()),
        "multi_seller_orders": int((facts["seller_count"] > 1).sum()),
    }
    (output / "quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    (output / "source_manifest.json").write_text(
        json.dumps(validate_source(source), indent=2), encoding="utf-8"
    )
    # This local-only training table joins outcomes solely to produce y. It is never replayed or published.
    training = facts[
        [
            "order_id",
            "order_purchase_timestamp",
            "order_estimated_delivery_date",
            "customer_state",
            "seller_state",
            "items_count",
            "seller_count",
            "order_value_brl",
            "freight_brl",
            "product_category_primary",
            "order_delivered_customer_date",
            "order_status",
        ]
    ].rename(
        columns={
            "order_purchase_timestamp": "event_ts",
            "order_estimated_delivery_date": "promised_delivery_date",
            "order_delivered_customer_date": "delivered_date",
            "order_status": "final_order_status",
        }
    )
    training.to_json(output / "facts.jsonl", orient="records", lines=True, date_format="iso")
    return quality
