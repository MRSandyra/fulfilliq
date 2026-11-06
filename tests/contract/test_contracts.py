import pytest

from fulfilliq.contracts import ContractError
from fulfilliq.transform import validate_batch


def placed(order_id="o-1", **values):
    return {
        "schema_version": 1,
        "event_type": "order_placed",
        "order_id": order_id,
        "event_ts": "2018-03-01T09:00:00",
        "promised_delivery_date": "2018-03-10",
        "customer_state": "SP",
        "seller_state": "RJ",
        "items_count": 1,
        "seller_count": 1,
        "order_value_brl": 10,
        "freight_brl": 2,
        "product_category_primary": "housewares",
        **values,
    }


def test_contract_rejects_future_fields_and_unknown_version():
    bad = placed(schema_version=999)
    with pytest.raises(ContractError, match="line 1"):
        validate_batch(__import__("json").dumps(bad) + "\n")  # DATA-015
    bad = placed(delivered_date="2018-03-11")
    with pytest.raises(ContractError):
        validate_batch(__import__("json").dumps(bad) + "\n")  # DATA-011


def test_contract_rejects_duplicate_and_negative_freight():
    import json

    with pytest.raises(ContractError, match="duplicate"):
        validate_batch(json.dumps(placed()) + "\n" + json.dumps(placed()) + "\n")
    with pytest.raises(ContractError):
        validate_batch(json.dumps(placed(freight_brl=-1)) + "\n")
