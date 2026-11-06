#!/usr/bin/env sh
set -eu
[ "${ALLOW_CLOUD_DEPLOY:-}" = "true" ] || { echo "Blocked: owner approval flag is required."; exit 1; }
echo "Deployment remains manual: review Terraform plan first. This script never applies infrastructure."
