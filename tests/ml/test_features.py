import pandas as pd

from fulfilliq.ml.features import FEATURES, feature_frame
from fulfilliq.ml.train import temporal_splits


def test_training_features_exclude_future_fields():
    facts = pd.DataFrame(
        [
            {
                "event_ts": "2018-01-01T09:00:00",
                "promised_delivery_date": "2018-01-10",
                "delivered_date": "2018-01-11",
                "final_order_status": "delivered",
                "customer_state": "SP",
                "seller_state": "RJ",
                "items_count": 1,
                "seller_count": 1,
                "order_value_brl": 10,
                "freight_brl": 2,
                "product_category_primary": "housewares",
                "order_status": "delivered",
                "review_score": 1,
            }
        ]
    )
    X, y, _ = feature_frame(facts)
    assert list(X.columns) == FEATURES and y.iloc[0] == 1  # ML-002 / ML-004
    assert "review_score" not in X.columns


def test_temporal_splits_are_disjoint():
    times = pd.Series(
        pd.to_datetime(
            ["2018-01-01", "2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05", "2018-01-06"]
        )
    )
    train, validation, test = temporal_splits(times)
    assert not (train & validation).any() and not (validation & test).any() and test.any()  # ML-001
