import json

import pytest

from fulfilliq.exports import DASHBOARD_PUBLIC_FILES, copy_dashboard_data


def _safe_payload(name: str) -> object:
    if name == "manifest.json":
        return {"schema_version": 1, "dataset_mode": "synthetic", "files": []}
    if name == "overview.json":
        return {"total_orders": 1, "eligible_delivered_orders": 1}
    if name == "quality.json":
        return {"label_coverage": 1, "definition": "aggregate only"}
    if name == "risk_summary.json":
        return {"model_available": False}
    return []


def _dashboard_input(tmp_path):
    source = tmp_path / "exports"
    source.mkdir()
    for name in DASHBOARD_PUBLIC_FILES:
        (source / name).write_text(json.dumps(_safe_payload(name)), encoding="utf-8")
    return source


def test_dashboard_export_rejects_row_level_identifier(tmp_path):
    source = _dashboard_input(tmp_path)
    (source / "sla_regions.json").write_text('[{"order_id":"private-order"}]')

    with pytest.raises(ValueError, match="privacy boundary"):
        copy_dashboard_data(source, tmp_path / "public", mode="synthetic")

    (source / "sla_regions.json").write_text('[{"customer_email":"private@example.com"}]')
    with pytest.raises(ValueError, match="privacy boundary"):
        copy_dashboard_data(source, tmp_path / "public", mode="synthetic")


def test_dashboard_export_rejects_unreviewed_json_and_stale_public_artifact(tmp_path):
    source = _dashboard_input(tmp_path)
    (source / "orders.json").write_text("[]")
    with pytest.raises(ValueError, match="unreviewed"):
        copy_dashboard_data(source, tmp_path / "public", mode="synthetic")

    (source / "orders.json").unlink()
    public = tmp_path / "public"
    (public / "old_order_export.json").write_text("[]")
    with pytest.raises(ValueError, match="stale"):
        copy_dashboard_data(source, public, mode="synthetic")
