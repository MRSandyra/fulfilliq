# ML training report: local Olist run

Run: 2026-11-06 UTC. Model: `logistic-regression-v1`; seed fixed in implementation. Dataset training hash: `65360bdce7398f41f9a574665f43ac5369e6c08bb884326feaf27f4dfb799811`.

Chronological split boundaries: train through 2018-02-26 (56,721 orders), validation 2018-02-27 through 2018-05-29 (20,876), test from 2018-05-30 (18,873).

| Held-out metric | Value |
|---|---:|
| ROC-AUC | 0.6815 |
| PR-AUC | 0.0671 |
| Brier score | 0.2543 |
| Precision | 0.0570 |
| Recall | 0.3670 |
| F1 | 0.0986 |
| Validation-selected threshold | 0.60 |
| Test positive prevalence | 0.0357 |

These are measured local results, not a claim of production model quality. The model binary and raw-score inputs remain ignored locally; the dashboard receives only aggregate score bins.
