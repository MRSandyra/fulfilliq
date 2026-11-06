# Deployment runbook

1. Confirm the account's Free Plan status, remaining credits, service/region support, and alerts in AWS Console; write a redacted receipt to `docs/evidence/cloud-preflight.md`.
2. Obtain explicit owner approval. Set `ALLOW_CLOUD_DEPLOY=true` only in the terminal for the bounded command.
3. Run `python scripts/aws_preflight.py`, then `terraform init`, `fmt -check`, `validate`, and a credentialed `terraform plan -out=planned.tfplan` in `infra/terraform`.
4. Owner reviews the exact plan and separately approves `terraform apply planned.tfplan`.
5. Upload no more than five unique synthetic batches after a dry run. Verify curated key, log evidence, Athena query ID, private bucket settings, and credits before/after.

Do not upgrade an account, use a paid plan, or run an apply because a budget alert exists.
