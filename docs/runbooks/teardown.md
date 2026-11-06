# Teardown (manual, owner-approved only)

Stop uploads, retain permitted aggregate evidence, list only this project bucket's prefixes, and inspect a destroy plan. `scripts/cleanup_cloud.py` intentionally stops at dry run. After backing up allowed material and obtaining a separate approval, remove scoped objects, apply a reviewed Terraform destroy, then verify that S3, Lambda, Athena results, IAM/OIDC roles and optional triggers are gone.
