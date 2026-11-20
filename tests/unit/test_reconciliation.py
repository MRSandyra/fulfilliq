import json

import pytest

from fulfilliq import reconciliation


def _local_export(tmp_path):
    overview = {
        "total_orders": 3,
        "eligible_delivered_orders": 2,
        "late_delivered_orders": 1,
        "late_delivery_rate": 0.5,
        "gmv_brl": 60.0,
        "undelivered_orders": 1,
    }
    (tmp_path / "overview.json").write_text(json.dumps(overview))
    return overview


def test_reconcile_cloud_emits_machine_readable_match(tmp_path, monkeypatch):
    overview = _local_export(tmp_path)
    monkeypatch.setattr(
        reconciliation.athena,
        "query_rows",
        lambda sql, *, workgroup: (
            "query-123",
            [{key: str(value) for key, value in overview.items()}],
        ),
    )

    result = reconciliation.reconcile_cloud(
        tmp_path, view="fulfilliq.v_order_delivery", workgroup="wg"
    )

    assert result["status"] == "MATCH"
    assert result["athena_query_execution_id"] == "query-123"
    assert all(metric["matches"] for metric in result["metrics"].values())


def test_reconcile_cloud_rejects_unsafe_identifier_and_reports_mismatch(tmp_path, monkeypatch):
    _local_export(tmp_path)
    with pytest.raises(ValueError, match="identifier"):
        reconciliation.reconcile_cloud(tmp_path, view="x; drop table x", workgroup="wg")
    monkeypatch.setattr(
        reconciliation.athena,
        "query_rows",
        lambda sql, *, workgroup: ("query-456", [{"total_orders": "4"}]),
    )
    result = reconciliation.reconcile_cloud(
        tmp_path, view="fulfilliq.v_order_delivery", workgroup="wg"
    )
    assert result["status"] == "MISMATCH"
