# Data lineage

`orders` supplies the order key, checkout time, promise, and completed-delivery facts. `order_items` is aggregated before the order join to produce counts, GMV and freight. Customer state comes through `customer_id`; product category and seller state are first joined at item level, then reduced deterministically. Preparation emits `order_placed` (checkout-only) and `delivery_outcome` (future label) JSONL separately. Local ingestion normalizes valid whole batches, quarantines invalid ones, then DuckDB reads curated objects into deduplicated order facts and aggregate exports.
