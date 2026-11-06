# Dataset validation: local run

Run: 2026-11-06 UTC using owner-supplied local Olist files.

| Table | Rows |
|---|---:|
| orders | 99,441 |
| order items | 112,650 |
| customers | 99,441 |
| products | 32,951 |
| sellers | 3,095 |

Required-file, header, duplicate-order, basic null, and foreign-key checks passed. Items without an order: 0. Orders without a customer: 0. Orders lacking delivered customer date: 2,965. The source manifest, including SHA-256 fingerprints, was written to ignored local output `data/prepared/olist/source_manifest.json`.

Preparation yielded 98,666 placement events and 96,470 delivered-outcome events. Multi-seller orders: 1,278. No raw records are copied into this evidence file.
