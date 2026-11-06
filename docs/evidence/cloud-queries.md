# Cloud queries

## Athena synthetic smoke: PASSED

Owner verification confirms that the Athena smoke test completed successfully in `ap-southeast-2` through the `fulfilliq-workgroup` workgroup.

| Check | Result |
|---|---:|
| `order_placed` rows / unique orders | 7 / 7 |
| `delivery_outcome` rows / unique orders | 7 / 7 |
| Inner-join matched orders | 7 |
| Athena DDL, Glue metadata, S3 access, and SQL execution | PASSED |

This evidence applies only to the seven-record synthetic smoke scope. Query IDs and scan-byte measurements were not recorded for that smoke run, so none are asserted for it. The later staged and full Olist reconciliation evidence appears below.

## Olist Stage 100: PASSED

The first isolated Olist stage used run ID `olist-2018-08-31-0100`. Its Athena tables point only to `curated/olist/olist-2018-08-31-0100/`; no smoke prefix is in scope.

| Check | Result | Athena query ID | Data scanned |
|---|---:|---|---:|
| `order_placed` rows / unique orders | 100 / 100 | `264251de-7d6e-4145-911c-000cd18775fb` | 32,635 bytes |
| `delivery_outcome` rows / unique orders | 86 / 86 | `3a0d0faf-1210-4dcf-b3f0-1f05d30c04da` | 23,220 bytes |
| Inner-join matched orders | 86 | `2fdf24d9-f31a-48d8-bfc8-b85314d1eba6` | 55,855 bytes |
| Stage late deliveries / rate | 3 / 3.4884% | same join query | same join query |

The two Stage 100 DDL queries both succeeded with zero bytes scanned: `b8faecc7-5ae4-4aea-8d23-36de480a7565` (placement) and `7616e76a-101f-459c-818c-d94daf31530b` (outcome). Curated-object ETags remained unchanged after an exact re-upload, and Lambda logged both batches as `duplicate`; no Stage 100 quarantine object exists.

This is a staged verification only. It is not a full Olist reconciliation and does not alter the frozen full-run target.

## Olist Stage 1,000: PASSED

The second isolated Olist stage used run ID `olist-2018-08-31-1000`. Its Athena tables point only to `curated/olist/olist-2018-08-31-1000/`; the synthetic smoke and Stage 100 prefixes are excluded.

| Check | Result | Athena query ID | Data scanned |
|---|---:|---|---:|
| `order_placed` rows / unique orders | 1,000 / 1,000 | `3c00d429-2b33-4dae-a6a7-b17cd49c5858` | 327,034 bytes |
| `delivery_outcome` rows / unique orders | 920 / 920 | `0d053b6d-b1ce-4061-9236-3475dd651129` | 248,400 bytes |
| Inner-join matched orders | 920 | `c0b08308-c95b-441a-a7f6-b723d03f49a9` | 575,434 bytes |
| Stage late deliveries / rate | 19 / 2.0652% | same join query | same join query |

The two Stage 1,000 DDL queries both succeeded with zero bytes scanned: `ee7ec67d-856e-4f14-ba4d-457eac0017e2` (placement) and `8ffff2b0-6cc8-4eb1-ba7b-83c62c03ef27` (outcome). A selected placement and outcome batch were each re-uploaded exactly once; both curated ETags were unchanged and Lambda logged `duplicate`. No Stage 1,000 quarantine object exists.

This is a staged verification only. The 98,665-order cloud reconciliation remains unexecuted and unclaimed.

## Full Olist reconciliation: PASSED

The full isolated run used `olist-2018-08-31-full`; its external tables read only `curated/olist/olist-2018-08-31-full/`. Smoke, Stage 100, and Stage 1,000 prefixes are excluded.

| Check | Actual cloud result | Athena query ID | Data scanned |
|---|---:|---|---:|
| `order_placed` rows / unique orders | 98,665 / 98,665 | `131d744c-8592-4319-825a-9e364b614a73` | 32,290,274 bytes |
| `delivery_outcome` rows / unique orders | 96,384 / 96,384 | `914f6cd2-2222-4284-90bd-5083855be5a1` | 26,023,680 bytes |
| Total / unique orders | 98,665 / 98,665 | `58f27037-7deb-407b-9ea3-3d09d21e0656` | 58,313,954 bytes |
| Eligible / unique eligible deliveries | 96,384 / 96,384 | same reconciliation query | same reconciliation query |
| Late eligible deliveries / rate | 6,466 / 0.06708582337317397 (6.7086% rounded) | same reconciliation query | same reconciliation query |

Both full-run DDL statements succeeded with zero bytes scanned: `c87df23d-d5d4-4bfe-8d67-a1d2bca02a66` (placement) and `0d71c9b5-d320-4f7d-8dff-fba1b908b5b0` (outcome). The three KPI queries scanned 116,627,908 bytes in total; every individual query remained below the 100 MiB workgroup cutoff.

There are 987 curated placement objects and 964 curated outcome objects, with zero full-run quarantine objects. An exact retry of one batch for each event type retained both curated ETags and Lambda logged `duplicate`. These actual results match the frozen local reference, so full cloud reconciliation is **PASSED**.
