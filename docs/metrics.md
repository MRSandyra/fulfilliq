# Metric contract

`total_orders` counts unique placement events. `eligible_delivered_orders` requires delivered status plus both delivery dates. `late_delivery_rate = late_delivered_orders / eligible_delivered_orders`; it is null, not 0%, when no order is eligible. GMV is the item-price sum aggregated before joining orders. Date trends use purchase date and say so explicitly.
