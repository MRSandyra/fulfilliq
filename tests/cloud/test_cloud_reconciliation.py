"""Opt-in, read-only check against the already-approved Athena KPI view."""

from __future__ import annotations

import json
import os

import pytest

from fulfilliq.reconciliation import reconcile_cloud

pytestmark = pytest.mark.skipif(
    os.getenv("CLOUD_TESTS") != "true",
    reason="set CLOUD_TESTS=true only in a credentialed, owner-approved environment",
)


def test_cloud_kpis_match_frozen_full_run_reference(tmp_path):
    if not os.getenv("FULFILLIQ_BUCKET"):
        pytest.fail("CLOUD_TESTS=true requires FULFILLIQ_BUCKET")
    reference = {
        "total_orders": 98665,
        "eligible_delivered_orders": 96384,
        "late_delivered_orders": 6466,
        "late_delivery_rate": 0.06708582337317397,
        "gmv_brl": 13591498.70,
        "undelivered_orders": 2281,
    }
    (tmp_path / "overview.json").write_text(json.dumps(reference), encoding="utf-8")
    result = reconcile_cloud(
        tmp_path, view="fulfilliq.v_order_delivery", workgroup="fulfilliq-workgroup"
    )
    assert result["status"] == "MATCH", json.dumps(result, indent=2)
