import json

from fulfilliq.replay import create_batches
from fulfilliq.transform import canonical_json


def placed(order_id: str, timestamp: str) -> dict:
    return {
        "schema_version": 1,
        "event_type": "order_placed",
        "order_id": order_id,
        "event_ts": timestamp,
        "promised_delivery_date": "2018-03-10",
        "customer_state": "SP",
        "seller_state": "RJ",
        "items_count": 1,
        "seller_count": 1,
        "order_value_brl": 10,
        "freight_brl": 2,
        "product_category_primary": "housewares",
    }


def outcome(order_id: str, timestamp: str) -> dict:
    return {
        "schema_version": 1,
        "event_type": "delivery_outcome",
        "order_id": order_id,
        "event_ts": timestamp,
        "promised_delivery_date": "2018-03-10",
        "delivered_date": "2018-03-09",
        "final_order_status": "delivered",
    }


def write_events(path, kind: str, events: list[dict]) -> None:
    (path / f"{kind}.jsonl").write_text(
        "\n".join(canonical_json(event) for event in events) + "\n", encoding="utf-8"
    )


def test_staged_replay_selects_a_nested_order_prefix_and_matching_outcomes(tmp_path):
    source = tmp_path / "prepared"
    source.mkdir()
    write_events(source, "order_placed", [placed("b", "2018-03-02T09:00:00"), placed("a", "2018-03-01T09:00:00")])
    write_events(source, "delivery_outcome", [outcome("b", "2018-03-04T09:00:00"), outcome("a", "2018-03-03T09:00:00")])

    output = tmp_path / "stage-1"
    create_batches(source, output, order_limit=1, max_records=100)

    staged_order = json.loads(next((output / "order_placed").glob("*.jsonl")).read_text())
    staged_outcome = json.loads(next((output / "delivery_outcome").glob("*.jsonl")).read_text())
    manifest = json.loads((output / "stage-manifest.json").read_text())
    assert staged_order["order_id"] == staged_outcome["order_id"] == "a"
    assert manifest["selected_orders"] == 1
    assert manifest["event_counts"] == {"order_placed": 1, "delivery_outcome": 1}
