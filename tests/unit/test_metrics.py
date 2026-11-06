from fulfilliq.metrics import is_late, kpis


def test_calendar_date_label_and_denominator():
    assert is_late("2018-03-10", "2018-03-10") is False  # DATA-008
    assert is_late("2018-03-11", "2018-03-10") is True
    report = kpis(
        [
            {
                "order_id": "a",
                "final_order_status": "delivered",
                "delivered_date": "2018-03-10",
                "promised_delivery_date": "2018-03-10",
                "order_value_brl": 10,
            },
            {
                "order_id": "b",
                "final_order_status": "delivered",
                "delivered_date": "2018-03-11",
                "promised_delivery_date": "2018-03-10",
                "order_value_brl": 20,
            },
            {
                "order_id": "c",
                "final_order_status": "canceled",
                "delivered_date": None,
                "promised_delivery_date": "2018-03-10",
                "order_value_brl": 30,
            },
        ]
    )
    assert report["late_delivery_rate"] == 0.5  # UI-003 / DATA-009
    assert report["total_orders"] == 3
    assert report["gmv_brl"] == 60
