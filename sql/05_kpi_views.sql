CREATE OR REPLACE VIEW fulfilliq.v_daily_sla AS
SELECT substr(event_ts,1,10) AS purchase_date, count(*) AS orders_placed,
 sum(eligible_delivery) AS eligible_delivered_orders, sum(delivery_late) AS late_delivered_orders,
 CAST(sum(delivery_late) AS double) / nullif(sum(eligible_delivery),0) AS late_delivery_rate,
 sum(order_value_brl) AS gmv_brl
FROM fulfilliq.v_order_delivery GROUP BY 1;
