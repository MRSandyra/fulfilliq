# Security posture

Raw CSVs, credentials, `.env` files, Terraform state, models, and order-level exports are ignored. The static dashboard contains only aggregates. Terraform specifies private/public-access-blocked SSE-S3 storage, a TLS-deny policy, prefix-scoped Lambda access, 7-day logs, and an Athena scan cap. The approved deployment demonstrated these controls; any future apply, upload, or cleanup remains gated by explicit owner approval and a temporary local flag.
