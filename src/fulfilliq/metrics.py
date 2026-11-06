from __future__ import annotations

from collections.abc import Iterable
from datetime import date


def is_late(delivered_date: str | date | None, promised_date: str | date | None) -> bool | None:
    """Return None when the order has no eligible completed-delivery label."""
    if delivered_date is None or promised_date is None:
        return None
    delivered = date.fromisoformat(str(delivered_date)[:10])
    promised = date.fromisoformat(str(promised_date)[:10])
    return delivered > promised


def kpis(rows: Iterable[dict]) -> dict[str, int | float | None]:
    unique: dict[str, dict] = {row["order_id"]: row for row in rows}
    values = list(unique.values())
    eligible = [
        r
        for r in values
        if r.get("final_order_status") == "delivered"
        and r.get("delivered_date")
        and r.get("promised_delivery_date")
    ]
    late = [r for r in eligible if is_late(r["delivered_date"], r["promised_delivery_date"])]
    gmv = sum(float(r.get("order_value_brl") or 0) for r in values)
    late_delays = [
        (
            date.fromisoformat(str(r["delivered_date"])[:10])
            - date.fromisoformat(str(r["promised_delivery_date"])[:10])
        ).days
        for r in late
    ]
    return {
        "total_orders": len(values),
        "eligible_delivered_orders": len(eligible),
        "late_delivered_orders": len(late),
        "late_delivery_rate": len(late) / len(eligible) if eligible else None,
        "undelivered_orders": len(values) - len(eligible),
        "gmv_brl": round(gmv, 2),
        "average_delay_days_late_only": sum(late_delays) / len(late_delays)
        if late_delays
        else None,
    }
