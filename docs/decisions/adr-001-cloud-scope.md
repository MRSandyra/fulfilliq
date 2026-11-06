# ADR-001: local-first, approval-gated cloud scope

## Decision

FulfillIQ uses deterministic local replay and DuckDB as its baseline. Terraform can declare a small S3/Lambda/Athena environment, but no plan/apply, upload, or cleanup may occur without owner approval and verified eligible Free Plan status.

## Consequences

The project can demonstrate reproducible processing without credentials. Cloud claims require actual, redacted AWS evidence; a missing cloud account remains `CLOUD DEPLOYMENT PENDING`, not a simulated success.
