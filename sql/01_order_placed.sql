CREATE EXTERNAL TABLE IF NOT EXISTS fulfilliq.raw_order_placed (
 schema_version int, event_type string, order_id string, event_ts string,
 promised_delivery_date string, customer_state string, seller_state string,
 items_count int, seller_count int, order_value_brl double, freight_brl double,
 product_category_primary string
) ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://<approved-bucket>/curated/order_placed/';
