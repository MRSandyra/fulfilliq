variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "project_id" {
  type    = string
  default = "fulfilliq"
}

variable "environment" {
  type        = string
  description = "Deployment boundary (for example dev, stage, or prod). Use a separate state key per value."
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,20}$", var.environment))
    error_message = "environment must be 2-20 lowercase letters, numbers, or hyphens."
  }
}

variable "bucket_name" {
  type        = string
  description = "Globally unique data bucket for this environment; never reuse across environments."

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be a valid 3-63 character S3 bucket name."
  }
}

variable "lambda_zip_path" {
  type    = string
  default = "../../artifacts/fulfilliq-lambda.zip"
}

variable "expiry_hint" {
  type    = string
  default = "MANUAL-TEARDOWN-REQUIRED"
}
