# Architecture

```text
Olist CSVs (local, ignored) → validation/order-level preparation → separate JSONL events
    → deterministic batches → local transform/quarantine → DuckDB aggregates → static dashboard
                                          └→ approved S3 → Lambda → Athena reconciliation path
```

The local path is the source of reproducible evidence. The approved cloud path uses the same contracts and pure transform code, never browser credentials. S3 event delivery is at-least-once, so deterministic curated keys, immutable write checks, and order-level warehouse deduplication prevent retry inflation; this is not a claim of global exactly-once processing.
