# ── VARIABLES ─────────────────────────────────────────────────────────────────
# SIMPLE EXPLANATION (like you're in school):
# Variables = Blanks you fill in before running Terraform.
# Like a form where you write your name, class, and school before submitting.

variable "aws_region" {
  description = "AWS region to deploy resources (ap-southeast-1 = Singapore)"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name used as a prefix for all AWS resource names"
  type        = string
  default     = "it-enablement"
}

variable "alert_email" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
}
