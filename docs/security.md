# Security posture

Raw CSVs, credentials, `.env` files, Terraform state, models, and order-level
exports are ignored. The approved deployment demonstrated the controls below;
future apply, upload, reconciliation, or cleanup remains gated by explicit owner
approval and a temporary local flag.

## Dashboard privacy boundary

`web/public/data/` is a browser-public boundary, not an access-controlled data
lake. It may contain only the reviewed aggregate files:

- `manifest.json`, `overview.json`, `quality.json`, `risk_summary.json`
- SLA aggregates by date, customer state, and product category

The exporter uses an allowlist and fails if an unknown JSON file is presented or
already remains in the output directory. It recursively rejects `order_id`,
customer/seller/product identifiers, contact/address/postal fields, raw model
scores, and delivery-date fields. This is deliberately fail-closed: new public
dimensions require code review, a privacy test, and a documented decision.

The dashboard has no AWS SDK, credentials, SQL endpoint, raw-event download, or
row-level drill-down. Aggregates can still present re-identification risk for
very small groups; this portfolio export is informational only and must not be
used as a substitute for a production disclosure-control policy (such as minimum
cell suppression and access control).

## Cloud and infrastructure boundary

Terraform specifies a private, public-access-blocked S3 bucket with enforced
bucket ownership, SSE-S3, HTTPS-only access, and seven-day expiry for Athena
result objects. Lambda has only exact raw read, curated immutable read/write,
quarantine write, and log-stream permissions; it has no wildcard bucket listing,
Athena, IAM, KMS, or secret-manager permission. There are no application secrets
in Lambda environment variables or Terraform outputs.

Terraform state is remote-only: `infra/terraform/backend.hcl.example` documents
the required separate private state bucket and lockfile. Backend config and
environment `.tfvars` remain ignored. Do not put credentials, access keys, or
source PII into Terraform variables, plans, CI logs, evidence JSON, or dashboard
exports. Use short-lived OIDC credentials in CI.
