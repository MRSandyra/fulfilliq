output "bucket_name" { value = aws_s3_bucket.pipeline.bucket }
output "lambda_function_name" { value = aws_lambda_function.transform.function_name }
output "athena_workgroup" { value = aws_athena_workgroup.fulfilliq.name }
output "region" { value = var.region }
