from fulfilliq.local_pipeline import ingest_batches
from fulfilliq.transform import canonical_json


def event():
    return {
        "schema_version": 1,
        "event_type": "order_placed",
        "order_id": "fixture-order",
        "event_ts": "2018-03-01T09:00:00",
        "promised_delivery_date": "2018-03-10",
        "customer_state": "SP",
        "seller_state": "RJ",
        "items_count": 1,
        "seller_count": 1,
        "order_value_brl": 10,
        "freight_brl": 2,
        "product_category_primary": "housewares",
    }


def test_local_ingest_idempotence_and_quarantine(tmp_path):
    source = tmp_path / "batches" / "order_placed"
    source.mkdir(parents=True)
    (source / "good.jsonl").write_text(canonical_json(event()) + "\n")
    (source / "bad.jsonl").write_text("{broken\n")
    output = tmp_path / "output"
    first = ingest_batches(tmp_path / "batches", output)
    second = ingest_batches(tmp_path / "batches", output)
    assert first["curated"] == 1 and first["quarantined"] == 1  # PIPE-006
    assert second["duplicates"] == 1
    assert (output / "quarantine" / "bad.json").exists()
