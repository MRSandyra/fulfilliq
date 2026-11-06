# Dashboard data smoke: local Olist run

Run: 2026-11-06 UTC from DuckDB local curated batches.

| KPI | Value |
|---|---:|
| Unique placed orders before cutoff | 98,665 |
| Eligible delivered orders | 96,384 |
| Late delivered orders | 6,466 |
| Late delivery rate | 6.7086% |
| GMV represented | BRL 13,591,498.70 |
| Label coverage | 97.6881% |
| Curated batches | 1,951 |
| Quarantined batches | 0 |
| Orphan outcomes | 0 |

`npm run lint`, `npm run test`, and `npm run build` passed after the safe export was copied to `web/public/data/`. The UI labels this as historical static data and has no AWS calls.
