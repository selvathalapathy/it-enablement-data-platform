# ── OUTPUTS ───────────────────────────────────────────────────────────────────
# SIMPLE EXPLANATION (like you're in school):
# Outputs = The receipt you get after Terraform finishes building.
# It tells you the names/addresses of what was just created so you can use them.

output "data_lake_bucket_name" {
  description = "Name of the S3 data lake bucket"
  value       = aws_s3_bucket.data_lake.bucket
}

output "data_lake_bucket_arn" {
  description = "ARN of the S3 data lake bucket"
  value       = aws_s3_bucket.data_lake.arn
}

output "sns_alerts_topic_arn" {
  description = "ARN of the SNS alerts topic"
  value       = aws_sns_topic.alerts.arn
}

output "lambda_role_arn" {
  description = "ARN of the IAM role assigned to Lambda functions"
  value       = aws_iam_role.lambda_role.arn
}

output "cloudwatch_dashboard_url" {
  description = "URL to view the CloudWatch dashboard in the AWS console"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
