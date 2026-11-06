from __future__ import annotations

import pandas as pd

FORBIDDEN_FEATURES = {
    "delivered_date",
    "final_order_status",
    "order_status",
    "order_delivered_customer_date",
    "order_approved_at",
    "order_delivered_carrier_date",
    "review_score",
}
FEATURES = [
    "purchase_month",
    "purchase_weekday",
    "promised_lead_days",
    "customer_state",
    "seller_state",
    "items_count",
    "seller_count",
    "order_value_brl",
    "freight_brl",
    "product_category_primary",
]


def feature_frame(facts: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    leaked = FORBIDDEN_FEATURES & set(facts.columns)
    # Labels may coexist in the training table, but cannot become X.
    working = facts.copy()
    purchase = pd.to_datetime(working["event_ts"])
    promise = pd.to_datetime(working["promised_delivery_date"])
    delivered = pd.to_datetime(working["delivered_date"])
    eligible = working["final_order_status"].eq("delivered") & delivered.notna() & promise.notna()
    working = working.loc[eligible].copy()
    purchase, promise, delivered = (
        purchase.loc[eligible],
        promise.loc[eligible],
        delivered.loc[eligible],
    )
    X = pd.DataFrame(
        {
            "purchase_month": purchase.dt.month,
            "purchase_weekday": purchase.dt.weekday,
            "promised_lead_days": (promise.dt.normalize() - purchase.dt.normalize()).dt.days,
            "customer_state": working["customer_state"].fillna("UNKNOWN"),
            "seller_state": working["seller_state"].fillna("UNKNOWN"),
            "items_count": working["items_count"],
            "seller_count": working["seller_count"],
            "order_value_brl": working["order_value_brl"],
            "freight_brl": working["freight_brl"],
            "product_category_primary": working["product_category_primary"].fillna("UNKNOWN"),
        }
    )
    assert list(X.columns) == FEATURES
    assert not leaked & set(X.columns)
    y = (delivered.dt.date > promise.dt.date).astype(int)
    return X, y, purchase
