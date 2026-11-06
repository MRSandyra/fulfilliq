CREATE OR REPLACE VIEW fulfilliq.v_order_delivery AS
SELECT p.*, o.delivered_date, o.final_order_status,
 CASE WHEN o.final_order_status='delivered' AND o.delivered_date IS NOT NULL AND p.promised_delivery_date IS NOT NULL THEN 1 ELSE 0 END AS eligible_delivery,
 CASE WHEN o.final_order_status='delivered' AND CAST(o.delivered_date AS date)>CAST(p.promised_delivery_date AS date) THEN 1 ELSE 0 END AS delivery_late
FROM fulfilliq.v_order_placed_dedup p LEFT JOIN fulfilliq.v_delivery_outcome_dedup o ON p.order_id=o.order_id;
