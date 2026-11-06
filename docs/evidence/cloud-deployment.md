# Cloud deployment

**DEPLOYED / SYNTHETIC CLOUD SMOKE PASSED.** During initial deployment on 2026-11-06 UTC, Terraform first stopped because AWS rejected a Lambda reserved concurrency of 2: it would leave fewer than the account-required 10 unreserved concurrent executions. The configuration was adjusted to omit that unsupported reservation.

The owner-approved recovery plan then replaced the tainted Lambda and completed the remaining resources: CloudWatch log group, inline IAM policy, S3 invoke permission, and raw-prefix S3 notification. Terraform reported 5 additions, 0 changes, and 1 destroyed Lambda replacement. No data was uploaded, Lambda invocation was tested, or Athena query executed yet.

Post-deploy read-only verification confirmed Lambda is `Active` with Python 3.12, 256 MB, and 30-second timeout; all four S3 public-access-block controls are true; bucket encryption is SSE-S3/AES256; and the Athena workgroup enforces its result location plus a 104,857,600-byte scan cap. Sensitive account identifiers are omitted from this evidence.

The initial smoke upload invoked Lambda twice but failed at import time because the first package contained Windows-native `pydantic_core` files. The log identifies `Runtime.ImportModuleError: No module named 'pydantic_core._pydantic_core'`. The package build was repaired to target `manylinux2014_x86_64` for Lambda's Python 3.12 runtime, then updated and retested successfully as recorded below.

The Linux-compatible code package was applied as one in-place Lambda update. A fresh pair of immutable synthetic raw keys then produced curated `order_placed` and `delivery_outcome` objects on the first poll. CloudWatch logs recorded 7 rows for each event type. Re-uploading the same placement object retained the curated object's ETag, proving deterministic idempotent output for that retry. The final credentialed Terraform drift check reported `No changes`.

The owner subsequently verified the Athena synthetic smoke in `ap-southeast-2` through `fulfilliq-workgroup`: DDL, Glue metadata, S3 access, and SQL execution passed, with 7 placement rows, 7 outcome rows, and 7 matched inner-join orders. This is not a full Olist reconciliation.

The approved staged replay then completed through 100-order, 1,000-order, and full isolated Olist scopes. The full scope produced 987 placement and 964 outcome curated objects, no quarantine objects, and retry-stable curated ETags. Athena reconciliation matched the frozen local reference: 98,665 total orders, 96,384 eligible deliveries, 6,466 late deliveries, and a 6.7086% late-delivery rate. A final credentialed Terraform plan reported `No changes`.
