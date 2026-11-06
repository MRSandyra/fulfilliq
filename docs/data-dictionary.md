# Data dictionary

| Field | Meaning / rule |
|---|---|
| `order_id` | Internal pipeline key; never included in public dashboard exports. |
| `event_ts` | Source clock timestamp with no claimed timezone. |
| `promised_delivery_date` | Date-only delivery promise known at checkout. |
| `delivery_late` | `1` only when delivered calendar date is later than promised calendar date. |
| `order_value_brl` | Sum of item prices per order; not payment total or profit. |
| `seller_state` | `MULTI` if an order has multiple sellers; otherwise its seller state. |
| `product_category_primary` | Highest-price item; ties by item then product ID; translated when available. |
