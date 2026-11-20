# Teardown (manual, owner-approved only)

1. Stop uploads and disable the CI cloud job or remove its OIDC role secret.
2. Retain only permitted aggregate evidence; do not copy raw events, customer
   data, credentials, or Terraform state into the repository.
3. List the exact project bucket and run-scoped `raw/`, `curated/`,
   `quarantine/`, and `athena-results/` prefixes. Confirm the environment and
   bucket name before deleting anything. `scripts/cleanup_cloud.py` is
   deliberately dry-run-only.
4. Empty only approved project objects, then run `terraform plan -destroy` with
   the matching remote backend config and environment tfvars. Review the plan:
   it must not include another environment's bucket, state bucket, or shared IAM
   identity.
5. After separate approval, apply the reviewed destroy plan. Verify removal of
   S3, Lambda, Lambda permission/notification, log group, Athena workgroup,
   project IAM role/policy, and any CI OIDC role created for this project.
6. Check AWS Cost Explorer/Budgets after the billing delay. The data bucket is
   intentionally not `force_destroy`; a failed destroy normally means objects
   still need a scoped, reviewed cleanup rather than that Terraform is safe to
   retry blindly.
