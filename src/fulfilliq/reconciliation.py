"""Machine-readable reconciliation of the frozen local KPI contract and Athena."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from . import athena

METRIC_KEYS = (
    "total_orders",
    "eligible_delivered_orders",
    "late_delivered_orders",
    "late_delivery_rate",
    "gmv_brl",
    "undelivered_orders",
)
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def _numeric(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"metric is not numeric: {value!r}") from exc


def reconcile_cloud(local_export: Path, *, view: str, workgroup: str) -> dict[str, Any]:
    """Compare local ``overview.json`` to one read-only Athena KPI query.

    ``athena.query_rows`` enforces the explicit cloud approval guard.  The
    identifier check keeps the only interpolated SQL fragment non-executable.
    """
    if not IDENTIFIER.fullmatch(view):
        raise ValueError("view must be a one- or two-part SQL identifier")
    local_path = local_export / "overview.json"
    local = json.loads(local_path.read_text(encoding="utf-8"))
    sql = (
        "SELECT count(*) AS total_orders, "
        "sum(eligible_delivery) AS eligible_delivered_orders, "
        "sum(delivery_late) AS late_delivered_orders, "
        "sum(delivery_late) * 1.0 / nullif(sum(eligible_delivery), 0) AS late_delivery_rate, "
        "sum(order_value_brl) AS gmv_brl, "
        "count(*) - sum(eligible_delivery) AS undelivered_orders "
        f"FROM {view}"
    )
    execution_id, rows = athena.query_rows(sql, workgroup=workgroup)
    if len(rows) != 1:
        raise RuntimeError(f"expected one Athena KPI row, got {len(rows)}")
    cloud = rows[0]
    metrics: dict[str, dict[str, object]] = {}
    for key in METRIC_KEYS:
        local_value, cloud_value = _numeric(local.get(key)), _numeric(cloud.get(key))
        # Decimal gives exact integer/currency comparisons and permits only a
        # tiny representation tolerance for Athena DOUBLE division.
        matches = (
            local_value == cloud_value
            if local_value is None or cloud_value is None
            else abs(local_value - cloud_value) <= Decimal("0.0000000001")
        )
        metrics[key] = {
            "local": local.get(key),
            "cloud": cloud.get(key),
            "matches": matches,
        }
    return {
        "status": "MATCH" if all(item["matches"] for item in metrics.values()) else "MISMATCH",
        "athena_query_execution_id": execution_id,
        "view": view,
        "metrics": metrics,
    }
