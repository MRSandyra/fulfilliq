# Cost controls

Cloud replay and Athena reconciliation are **VERIFIED**. The design has no VPC,
NAT, EC2, RDS, Redshift, Glue jobs/crawlers, or managed Kafka. The approved full
run's three Athena KPI queries scanned 116,627,908 bytes in total, with each
query below the 100 MiB workgroup cutoff. A before/after billing balance was not
captured, so this is not a zero-cost claim; see `docs/evidence/cost-checks.md`.

Potential charges remain: S3 object storage/requests, Lambda invocations and
duration, CloudWatch Logs retention, Athena bytes scanned (including the
credentialed reconciliation query), and the separately administered Terraform
state bucket. Athena result objects now expire after seven days, but raw,
curated, and quarantine evidence is retained until an owner-approved scoped
teardown. Set an AWS Budget/alert before any replay, use the 100 MiB Athena cap,
run the smallest staged scope first, and never leave experimental run prefixes
unreviewed.
