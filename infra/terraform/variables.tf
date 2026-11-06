variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "project_id" {
  type    = string
  default = "fulfilliq"
}

variable "bucket_name" { type = string }

variable "lambda_zip_path" {
  type    = string
  default = "../../artifacts/fulfilliq-lambda.zip"
}

variable "expiry_hint" {
  type    = string
  default = "MANUAL-TEARDOWN-REQUIRED"
}
