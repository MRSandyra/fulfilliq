from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create publishable fabricated Olist-shaped fixtures"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    orders = [
        [
            "fixture-order-a",
            "customer-a",
            "delivered",
            "2018-03-01 09:00:00",
            "2018-03-01 10:00:00",
            "2018-03-02 09:00:00",
            "2018-03-10 00:00:00",
            "2018-03-10 00:00:00",
        ],
        [
            "fixture-order-b",
            "customer-b",
            "delivered",
            "2018-03-01 10:00:00",
            "2018-03-01 10:10:00",
            "2018-03-02 09:00:00",
            "2018-03-11 00:00:00",
            "2018-03-10 00:00:00",
        ],
        [
            "fixture-order-c",
            "customer-c",
            "canceled",
            "2018-03-02 10:00:00",
            None,
            None,
            None,
            "2018-03-12 00:00:00",
        ],
        [
            "fixture-order-d",
            "customer-d",
            "shipped",
            "2018-03-03 10:00:00",
            "2018-03-03 11:00:00",
            None,
            None,
            "2018-03-13 00:00:00",
        ],
        [
            "fixture-order-e",
            "customer-e",
            "delivered",
            "2018-04-01 10:00:00",
            "2018-04-01 11:00:00",
            "2018-04-02 09:00:00",
            "2018-04-15 00:00:00",
            "2018-04-10 00:00:00",
        ],
        [
            "fixture-order-f",
            "customer-f",
            "delivered",
            "2018-05-01 10:00:00",
            "2018-05-01 11:00:00",
            "2018-05-02 09:00:00",
            "2018-05-20 00:00:00",
            "2018-05-16 00:00:00",
        ],
        [
            "fixture-order-g",
            "customer-g",
            "delivered",
            "2018-06-01 10:00:00",
            "2018-06-01 11:00:00",
            "2018-06-02 09:00:00",
            "2018-06-20 00:00:00",
            "2018-06-18 00:00:00",
        ],
        [
            "fixture-order-h",
            "customer-h",
            "delivered",
            "2018-07-01 10:00:00",
            "2018-07-01 11:00:00",
            "2018-07-02 09:00:00",
            "2018-07-25 00:00:00",
            "2018-07-20 00:00:00",
        ],
        [
            "fixture-order-i",
            "customer-i",
            "delivered",
            "2018-08-01 10:00:00",
            "2018-08-01 11:00:00",
            "2018-08-02 09:00:00",
            "2018-08-30 00:00:00",
            "2018-08-20 00:00:00",
        ],
    ]
    columns = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    pd.DataFrame(orders, columns=columns).to_csv(
        args.output / "olist_orders_dataset.csv", index=False
    )
    customers = [
        [f"customer-{chr(97 + i)}", f"unique-{i}", state]
        for i, state in enumerate(["SP", "RJ", "MG", "BA", "SP", "RJ", "RS", "SC", "PR"])
    ]
    pd.DataFrame(customers, columns=["customer_id", "customer_unique_id", "customer_state"]).to_csv(
        args.output / "olist_customers_dataset.csv", index=False
    )
    items = [
        ["fixture-order-a", 1, "product-a", "seller-a", "2018-03-05 00:00:00", 10, 3],
        ["fixture-order-b", 1, "product-b", "seller-b", "2018-03-05 00:00:00", 20, 5],
        ["fixture-order-e", 1, "product-e", "seller-a", "2018-04-05 00:00:00", 10, 3],
        ["fixture-order-e", 2, "product-f", "seller-b", "2018-04-05 00:00:00", 20, 5],
    ]
    for letter, price in [("f", 40), ("g", 50), ("h", 60), ("i", 70)]:
        items.append(
            [
                f"fixture-order-{letter}",
                1,
                f"product-{letter}",
                "seller-a",
                "2018-05-05 00:00:00",
                price,
                8,
            ]
        )
    pd.DataFrame(
        items,
        columns=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    ).to_csv(args.output / "olist_order_items_dataset.csv", index=False)
    products = [[f"product-{letter}", "housewares"] for letter in "abefghi"]
    pd.DataFrame(products, columns=["product_id", "product_category_name"]).to_csv(
        args.output / "olist_products_dataset.csv", index=False
    )
    pd.DataFrame(
        [["seller-a", "00000", "SP"], ["seller-b", "11111", "RJ"]],
        columns=["seller_id", "seller_zip_code_prefix", "seller_state"],
    ).to_csv(args.output / "olist_sellers_dataset.csv", index=False)
    pd.DataFrame(
        [["housewares", "housewares"]],
        columns=["product_category_name", "product_category_name_english"],
    ).to_csv(args.output / "product_category_name_translation.csv", index=False)


if __name__ == "__main__":
    main()
