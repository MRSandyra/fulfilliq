CREATE OR REPLACE VIEW fulfilliq.v_order_placed_dedup AS
SELECT * FROM (SELECT *, row_number() OVER (PARTITION BY order_id ORDER BY event_ts) rn FROM fulfilliq.raw_order_placed) WHERE rn = 1;
CREATE OR REPLACE VIEW fulfilliq.v_delivery_outcome_dedup AS
SELECT * FROM (SELECT *, row_number() OVER (PARTITION BY order_id ORDER BY event_ts) rn FROM fulfilliq.raw_delivery_outcome) WHERE rn = 1;
