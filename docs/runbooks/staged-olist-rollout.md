# Staged full Olist replay rollout

## Status and boundary

**All approved stages passed, including the full reconciliation.** The seven-record synthetic Athena smoke remains separate evidence. This runbook never treats that smoke data as Olist evidence.

The frozen reconciliation target is the existing local reference generated with the exact replay cutoff `--as-of 2018-08-31`: **98,665 placed orders, 96,384 eligible deliveries, and a 6.7086% late-delivery rate** (6,466 late eligible deliveries before rounding). Before rollout, these were targets rather than cloud results. The final cloud query outputs, execution IDs, and scan bytes are now recorded and match in `docs/evidence/cloud-queries.md`.

## Replay design and ordering review

`replay` reads each event stream in ascending `(event_ts, order_id)` order. A staged run selects the first N `order_placed` records at the frozen cutoff, then keeps only `delivery_outcome` records whose `order_id` is in that selected prefix; outcome rows retain their own timestamp order. The stages are therefore nested: 100 is a prefix of 1,000, and 1,000 is a prefix of 98,665.

Batch files are canonical JSONL, capped at 100 rows or 256 KiB, and named from a content hash. The new `stage-manifest.json` records the cutoff, requested order limit, selected counts, and batch hashes. A staged output directory must be new and empty, preventing accidental mixing of two stage definitions.

Upload planning is deterministic and sends every `order_placed` batch before any `delivery_outcome` batch. S3 notifications themselves are at-least-once and cross-object execution order is not guaranteed; that is safe because Lambda validates each whole batch independently and Athena runs only after the stage manifest, curated-object counts, and quarantine count are checked.

## Isolation from the smoke test

Synthetic smoke remains on the legacy prefixes `raw/<event-type>/` and `curated/<event-type>/`. Every Olist stage uses a unique run ID and these prefixes:

```text
raw/olist/<run-id>/<event-type>/<batch-id>.jsonl
curated/olist/<run-id>/<event-type>/<batch-id>.jsonl
quarantine/olist/<run-id>/<batch-id>.json
```

The deployed Lambda adapter enforces that the event type agrees with its raw-key prefix and writes the corresponding namespaced curated key. It performs a read-before-write immutability check: an identical retry is reported as a duplicate; different content under an existing curated key is quarantined instead of overwriting evidence. Include this protection in any reviewed future Lambda deployment.

For each stage, create Athena external tables whose `LOCATION` is exactly that stage's `curated/olist/<run-id>/...` prefix. Never define a full-replay table over `curated/` or over the smoke prefixes. Drop the stage-specific table metadata after a failed stage; do not use a broad wildcard location.

## Reproducible stages

Generate locally only after approval, in new directories. These commands create files locally; the separate `upload-events --mode apply` command remains approval-gated by `ALLOW_CLOUD_DEPLOY=true`.

| Stage | Run ID | Planned placement / outcome rows | Raw batches | Raw JSONL bytes |
|---|---|---:|---:|---:|
| 100 orders | `olist-2018-08-31-0100` | 100 / 86 | 1 / 1 | 52,673 |
| 1,000 orders | `olist-2018-08-31-1000` | 1,000 / 920 | 10 / 10 | 541,394 |
| Full | `olist-2018-08-31-full` | 98,665 / 96,384 | 987 / 964 | 54,747,746 |

Stage 100 actual cloud result: 100 placement rows / 100 unique orders, 86 outcome rows / 86 unique orders, and 86 inner-join matches. Both DDL statements succeeded; Athena scan bytes were 32,635, 23,220, and 55,855 for the placement, outcome, and join queries respectively. The two exact retry probes retained curated ETags and logged `duplicate`; quarantine was empty. Evidence is recorded in `docs/evidence/cloud-queries.md`.

Stage 1,000 actual cloud result: 1,000 placement rows / 1,000 unique orders, 920 outcome rows / 920 unique orders, and 920 inner-join matches. Both DDL statements succeeded; Athena scan bytes were 327,034, 248,400, and 575,434 for the placement, outcome, and join queries respectively. One exact placement retry and one exact outcome retry retained curated ETags and logged `duplicate`; quarantine was empty. Evidence is recorded in `docs/evidence/cloud-queries.md`.

Full-stage actual cloud result: 98,665 placement rows / unique orders, 96,384 outcome rows / unique orders, 96,384 eligible deliveries, and 6,466 late deliveries at a 0.06708582337317397 rate (6.7086% rounded). Both full DDL statements succeeded; the three Athena KPI queries scanned 32,290,274, 26,023,680, and 58,313,954 bytes. The isolated run produced 987 placement and 964 outcome curated objects with no quarantine. One exact placement retry and one exact outcome retry retained curated ETags and logged `duplicate`. This matches the frozen local reference; evidence is recorded in `docs/evidence/cloud-queries.md`.

```powershell
python -m fulfilliq.cli replay --input data/prepared/olist --output data/batches/olist-stage-0100 --as-of 2018-08-31 --max-records 100 --order-limit 100
python -m fulfilliq.cli replay --input data/prepared/olist --output data/batches/olist-stage-1000 --as-of 2018-08-31 --max-records 100 --order-limit 1000
python -m fulfilliq.cli replay --input data/prepared/olist --output data/batches/olist-stage-full --as-of 2018-08-31 --max-records 100 --order-limit 98665
```

For each stage, first run a dry run and inspect the returned keys. The approved apply command must use the matching source directory, run ID, and exact batch count. The uploader will not perform an apply without the temporary owner-set `ALLOW_CLOUD_DEPLOY=true` guard.

```powershell
python -m fulfilliq.cli upload-events --source data/batches/olist-stage-0100 --mode dry-run --limit-batches 2 --run-id olist-2018-08-31-0100
```

Proceed from 100 to 1,000 to full only when the preceding stage's gates pass:

1. `stage-manifest.json` reports the planned row counts and no unexpected local files exist.
2. The number of curated objects equals the stage batch count, quarantine is zero, and Lambda logs have one valid result per unique batch. Repeat exactly one placement and one outcome raw upload; both must return `duplicate`, keep the curated ETag/content unchanged, and leave Athena row counts unchanged.
3. Stage-scoped Athena checks show expected placement rows and unique orders, expected outcome rows and unique orders, and an inner join equal to the outcome count (86, 920, then 96,384). Capture query execution IDs and `DataScannedInBytes`.
4. For the full stage only, the KPI query must show 98,665 total orders, 96,384 eligible deliveries, 6,466 late eligible deliveries, and `late_delivery_rate = 0.067086` (6.7086% rounded). A mismatch stops promotion and starts rollback; it is not reconciled by changing the target.

## Estimated request volume and credit exposure

The estimates below use the actual staged JSONL byte counts above and assume one successful S3 notification per raw object. The Lambda configuration is 256 MB and 30 seconds.

| Stage | Raw uploads / minimum Lambda invokes | Baseline S3 object API operations* | Three KPI-query scan allowance | Conservative Lambda duration ceiling |
|---|---:|---:|---:|---:|
| 100 | 2 / 2 | 8 | 30 MB minimum | 15 GB-s |
| 1,000 | 20 / 20 | 80 | 30 MB minimum | 150 GB-s |
| Full | 1,951 / 1,951 | 7,804 | about 164 MB total | 14,633 GB-s |

\*Per batch: raw PUT, Lambda raw GET, immutable curated-key GET, curated PUT. It excludes S3 event delivery internals, CloudWatch logs, Athena result objects, and deliberately repeated retry probes.

The Athena allowance assumes JSON queries scan the full stage payload on each of three KPI queries. The full per-query payload is about 54.75 MB, below the deployed 100 MiB workgroup cutoff. Athena SQL pricing is based on bytes scanned, at USD 5/TB with a 10 MB minimum per query; DDL is not charged. Lambda is billed by requests and GB-seconds and documents a 1M-request / 400,000-GB-second monthly free tier. S3 request and storage pricing is region-dependent. Therefore the expected Olist replay consumption is cents and conservatively well below USD 0.50 of the USD 100 credit balance, excluding unplanned queries, retained logs, or other account workloads. Record the billing dashboard balance before and after every stage; this is an estimate, not a zero-cost guarantee. [Athena pricing](https://aws.amazon.com/athena/pricing/) and [Lambda pricing](https://aws.amazon.com/lambda/pricing/).

## Stop, rollback, and cleanup

1. **Stop first:** do not launch the next upload command; unset `ALLOW_CLOUD_DEPLOY`; preserve the stage manifest, uploader key list, Lambda log references, object ETags, query IDs, scan bytes, and error reports.
2. **Contain only with approval:** if duplicate, quarantine, count, or KPI gates fail, disable further writes. Changing the deployed notification or Lambda code is an infrastructure write and requires a separately reviewed Terraform plan and owner approval.
3. **Forensic cleanup:** after preserving evidence and receiving approval, remove only the exact run-scoped raw, curated, and quarantine prefixes for the failed `<run-id>`, then drop only that run's Athena table/view metadata. Never delete the legacy smoke prefixes, another stage's run ID, the bucket root, or the whole workgroup.
4. **Athena results:** retain the captured query IDs. Delete result objects only by their exact recorded keys or allow an approved lifecycle rule; do not broadly clear `athena-results/` because it may contain evidence from other runs.
5. **Retry:** correct the defect, create a new run ID and a fresh local stage directory, run the two duplicate probes again, and restart from the smallest failed stage. Do not overwrite a prior run to force a match.
