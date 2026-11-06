# Terraform validation: local run

Run: 2026-11-06 UTC using Terraform v1.17.0.

- `terraform -chdir=infra/terraform fmt -check -recursive`: passed.
- `terraform -chdir=infra/terraform init -backend=false`: passed; installed signed `hashicorp/aws` v5.100.0 and generated `.terraform.lock.hcl`.
- `terraform -chdir=infra/terraform validate`: passed.

This is the historic static-validation record only. Later owner-approved credentialed plans/applies, Lambda deployment, and Athena queries were executed; see `cloud-deployment.md` and `cloud-queries.md`.
