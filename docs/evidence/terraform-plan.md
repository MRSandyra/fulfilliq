# Terraform plan: reviewed, not applied

Run: 2026-11-06 UTC, owner-authenticated session, region `ap-southeast-2`.

`terraform init -backend=false`, `terraform validate`, and credentialed `terraform plan` succeeded. The local plan reports **11 to add, 0 to change, 0 to destroy**.

The plan does not include prohibited services such as EC2, RDS, NAT Gateway, Redshift, Glue jobs/crawlers, or managed Kafka. It creates a single private SSE-S3 bucket, scoped Lambda/IAM/logging, an Athena workgroup with 100 MiB scan cap, and the exact S3-to-Lambda notification. The saved plan is ignored by Git and must be reviewed again immediately before any apply because the temporary AWS session can expire.

**No apply was run.** An apply requires a separate explicit owner instruction after this plan review.
