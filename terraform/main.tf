# AWS Infrastructure — IT Enablement Data Platform
# ================================================
#
# SIMPLE EXPLANATION (like you're in school):
# Terraform = A blueprint for building a house.
# Instead of manually building each room (AWS service),
# you write the blueprint once and Terraform builds everything for you.
#
# What we're building:
# 1. S3 Bucket    = A big filing cabinet to store data
# 2. Lambda       = A small helper that runs Python code automatically
# 3. CloudWatch   = A security guard that monitors everything
# 4. IAM Role     = A security badge giving Lambda permission to access S3
# 5. SNS Topic    = A notification system (like a school PA system)

# ── PROVIDER ─────────────────────────────────────────────────────────────────
# Tell Terraform we're using AWS in Singapore region
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region  # ap-southeast-1 = Singapore

  default_tags {
    tags = {
      Project     = "IT-Enablement-Data-Platform"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "IT-Enablement-Team"
    }
  }
}


# ── S3 DATA LAKE ─────────────────────────────────────────────────────────────
# S3 = Amazon Simple Storage Service = A big cloud filing cabinet
# We use 3 zones like a school's filing system:
# - raw/       = Original data (like rough notes)
# - processed/ = Cleaned data (like neat notes)
# - curated/   = Final reports (like the printed report card)

resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-lake"
}

# Enable versioning — keeps old copies of files
# Like keeping all drafts of an essay, not just the final version
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt all data at rest
# Like putting all files in a locked cabinet
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access — only our systems can read the data
# Like making sure only teachers can access student records
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Auto-delete old files to save costs
# Like cleaning out old homework after the school year ends
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "raw-data-lifecycle"
    status = "Enabled"
    filter { prefix = "raw/" }
    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # Cheaper storage after 30 days
    }
    expiration {
      days = 90  # Delete raw data after 90 days
    }
  }

  rule {
    id     = "processed-data-lifecycle"
    status = "Enabled"
    filter { prefix = "processed/" }
    transition {
      days          = 90
      storage_class = "GLACIER"  # Very cheap archive after 90 days
    }
  }
}


# ── IAM ROLE FOR LAMBDA ───────────────────────────────────────────────────────
# IAM = Identity and Access Management = Security badges
# Lambda needs a badge to say "I am allowed to access S3 and CloudWatch"
# Like a teacher's ID card that gives them access to the staff room

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Allow Lambda to read/write S3
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"]
        Resource = ["${aws_s3_bucket.data_lake.arn}", "${aws_s3_bucket.data_lake.arn}/*"]
      },
      {
        # Allow Lambda to write logs and metrics
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData", "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      },
      {
        # Allow Lambda to read secrets (API keys stored securely)
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_name}/*"
      }
    ]
  })
}


# ── SNS NOTIFICATION TOPIC ────────────────────────────────────────────────────
# SNS = Simple Notification Service = School PA (Public Address) system
# When an alarm goes off, SNS broadcasts the message to subscribers (email, Slack)

resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"
}

resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email  # Who receives the alerts
}


# ── CLOUDWATCH LOG GROUP ─────────────────────────────────────────────────────
# CloudWatch Logs = A diary for the application
# Every time something happens (error, success), it gets written here

resource "aws_cloudwatch_log_group" "etl_logs" {
  name              = "/it-enablement/${var.environment}/etl-pipeline"
  retention_in_days = 30  # Keep logs for 30 days
}

resource "aws_cloudwatch_log_group" "api_extractor_logs" {
  name              = "/it-enablement/${var.environment}/api-extractor"
  retention_in_days = 30
}


# ── CLOUDWATCH ALARMS ─────────────────────────────────────────────────────────
# Alarms = Fire alarms for the IT system
# When something goes wrong, the alarm fires and sends a notification

resource "aws_cloudwatch_metric_alarm" "etl_failure" {
  alarm_name          = "${var.project_name}-etl-failure"
  alarm_description   = "ETL pipeline failed to complete"
  metric_name         = "ETLSuccess"
  namespace           = "ITEnablement/ETL"
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"

  dimensions = {
    Pipeline = "TransactionETL"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Severity = "HIGH"
  }
}

resource "aws_cloudwatch_metric_alarm" "etl_slow" {
  alarm_name          = "${var.project_name}-etl-duration-high"
  alarm_description   = "ETL taking longer than 30 minutes"
  metric_name         = "ETLDurationSeconds"
  namespace           = "ITEnablement/ETL"
  statistic           = "Average"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 1800
  comparison_operator = "GreaterThanThreshold"

  dimensions = {
    Pipeline = "TransactionETL"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = {
    Severity = "MEDIUM"
  }
}


# ── CLOUDWATCH DASHBOARD ──────────────────────────────────────────────────────
# Dashboard = A single screen showing the health of everything
# Like a school's notice board showing attendance, grades, announcements

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title   = "ETL Pipeline Success"
          metrics = [["ITEnablement/ETL", "ETLSuccess", "Pipeline", "TransactionETL"]]
          period  = 3600
          stat    = "Sum"
          view    = "timeSeries"
        }
      },
      {
        type = "metric"
        properties = {
          title   = "Rows Processed"
          metrics = [["ITEnablement/ETL", "ETLRowsProcessed", "Pipeline", "TransactionETL"]]
          period  = 86400
          stat    = "Sum"
          view    = "bar"
        }
      },
      {
        type = "alarm"
        properties = {
          title  = "System Alarms"
          alarms = [aws_cloudwatch_metric_alarm.etl_failure.arn, aws_cloudwatch_metric_alarm.etl_slow.arn]
        }
      }
    ]
  })
}
