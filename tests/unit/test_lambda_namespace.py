import importlib.util
import json
from io import BytesIO
from pathlib import Path


class FakeS3:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects
        self.puts: list[str] = []

    def get_object(self, *, Bucket, Key):
        return {"Body": BytesIO(self.objects[Key])}

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body
        self.puts.append(Key)


def load_handler():
    path = Path(__file__).parents[2] / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("fulfilliq_lambda_handler", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.handler


def test_namespaced_olist_event_is_written_outside_the_smoke_prefix():
    event = {
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
    raw_key = "raw/olist/olist-2018-08-31-100/order_placed/batch.jsonl"
    s3 = FakeS3({raw_key: (json.dumps(event) + "\n").encode()})
    invoke_event = {"Records": [{"s3": {"bucket": {"name": "bucket"}, "object": {"key": raw_key}}}]}

    response = load_handler()(invoke_event, None, s3_client=s3)

    assert response["records"][0]["status"] == "curated"
    assert "curated/olist/olist-2018-08-31-100/order_placed/batch.jsonl" in s3.objects
    assert "curated/order_placed/batch.jsonl" not in s3.objects

    duplicate = load_handler()(invoke_event, None, s3_client=s3)
    assert duplicate["records"][0]["status"] == "duplicate"
    assert s3.puts == ["curated/olist/olist-2018-08-31-100/order_placed/batch.jsonl"]
