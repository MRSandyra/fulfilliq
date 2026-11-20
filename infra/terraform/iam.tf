data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project_id}-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "lambda" {
  statement {
    actions = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.pipeline.arn}/raw/order_placed/*.jsonl",
      "${aws_s3_bucket.pipeline.arn}/raw/delivery_outcome/*.jsonl",
      "${aws_s3_bucket.pipeline.arn}/raw/olist/*/order_placed/*.jsonl",
      "${aws_s3_bucket.pipeline.arn}/raw/olist/*/delivery_outcome/*.jsonl",
    ]
  }
  statement {
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = [
      "${aws_s3_bucket.pipeline.arn}/curated/order_placed/*.jsonl",
      "${aws_s3_bucket.pipeline.arn}/curated/delivery_outcome/*.jsonl",
      "${aws_s3_bucket.pipeline.arn}/curated/olist/*/order_placed/*.jsonl",
      "${aws_s3_bucket.pipeline.arn}/curated/olist/*/delivery_outcome/*.jsonl",
    ]
  }
  statement {
    actions = ["s3:PutObject"]
    resources = [
      "${aws_s3_bucket.pipeline.arn}/quarantine/*.json",
      "${aws_s3_bucket.pipeline.arn}/quarantine/olist/*/*.json",
    ]
  }
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${var.project_id}-least-privilege"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}
