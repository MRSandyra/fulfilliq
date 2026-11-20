terraform {
  required_version = ">= 1.6.0"

  # Backend arguments are intentionally supplied with -backend-config from an
  # ignored environment-specific file. State must never be committed locally.
  backend "s3" {}

  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
