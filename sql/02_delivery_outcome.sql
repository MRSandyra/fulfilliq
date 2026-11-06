CREATE EXTERNAL TABLE IF NOT EXISTS fulfilliq.raw_delivery_outcome (
 schema_version int, event_type string, order_id string, event_ts string,
 delivered_date string, promised_delivery_date string, final_order_status string
) ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://<approved-bucket>/curated/delivery_outcome/';
