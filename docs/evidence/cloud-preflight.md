# Cloud preflight

**Historic preflight record: deployment subsequently completed.**

At the time this preflight record was created, no AWS identity, Free account plan, credit balance, region eligibility, Terraform plan, resource creation, or cloud query had been performed. The owner later completed the checklist, approved the plans, and the deployment/reconciliation completed; see `cloud-deployment.md` and `cloud-queries.md`.

## Tooling verification: 2026-11-06 UTC

- Terraform 1.17.0: `fmt -check -recursive`, `init -backend=false`, and `validate` passed with `hashicorp/aws` 5.100.0.
- AWS CLI 2.39.5: installed and callable.
- Read-only `aws sts get-caller-identity` and the project preflight could not locate AWS credentials. No identity, plan type, credits, supported-service status, or region could therefore be verified.

This confirms configuration syntax only; it is not cloud preflight approval and does not authorize Terraform plan/apply.

## Identity check: 2026-11-06 UTC

The owner-authenticated `fulfilliq-dev` profile completed a read-only STS identity check successfully. The owner confirmed an eligible Free Plan, USD 100 credit, and service permission, and selected `ap-southeast-2`; Terraform now uses that region by default. This permits only the reviewed credentialed plan at this stage, not an apply.

## Credentialed plan: 2026-11-06 UTC

With the owner-approved temporary session, Terraform created a local, Git-ignored plan file. It reports **11 additions, 0 changes, 0 deletions**. The planned surface is limited to the declared S3 pipeline bucket (private, SSE-S3, HTTPS-only and public-access-blocked), Lambda (Python 3.12, 256 MB, 30 seconds, concurrency 2), scoped IAM role/policy, Lambda log group with 7-day retention, S3 event notification for `raw/*.jsonl`, Lambda invoke permission, and an Athena workgroup with a 100 MiB per-query scan cutoff. No resource was created.
