locals {
  tags = {
    Project     = "FulfillIQ"
    Environment = "dev"
    Owner       = "portfolio"
    Purpose     = "learning"
    ExpiryHint  = var.expiry_hint
  }
}

resource "aws_s3_bucket" "pipeline" { bucket = var.bucket_name }

resource "aws_s3_bucket_public_access_block" "pipeline" {
  bucket                  = aws_s3_bucket.pipeline.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pipeline" {
  bucket = aws_s3_bucket.pipeline.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.pipeline.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.pipeline.arn, "${aws_s3_bucket.pipeline.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

resource "aws_lambda_function" "transform" {
  function_name                  = "${var.project_id}-transform"
  role                           = aws_iam_role.lambda.arn
  runtime                        = "python3.12"
  handler                        = "handler.handler"
  filename                       = var.lambda_zip_path
  source_code_hash               = filebase64sha256(var.lambda_zip_path)
  memory_size                    = 256
  timeout                        = 30
  # This account enforces a minimum unreserved concurrency of 10. A reservation
  # of 2 is therefore not permitted; no reservation is safer than a rejected deploy.
  environment {
    variables = {
      FULFILLIQ_BUCKET = aws_s3_bucket.pipeline.bucket
      LOG_LEVEL        = "INFO"
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.transform.function_name}"
  retention_in_days = 7
}

resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transform.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.pipeline.arn
}

resource "aws_s3_bucket_notification" "raw" {
  bucket = aws_s3_bucket.pipeline.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.transform.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
    filter_suffix       = ".jsonl"
  }
  depends_on = [aws_lambda_permission.s3]
}

resource "aws_athena_workgroup" "fulfilliq" {
  name = "${var.project_id}-workgroup"
  configuration {
    enforce_workgroup_configuration = true
    bytes_scanned_cutoff_per_query  = 104857600
    result_configuration {
      output_location = "s3://${aws_s3_bucket.pipeline.bucket}/athena-results/"
    }
  }
}
