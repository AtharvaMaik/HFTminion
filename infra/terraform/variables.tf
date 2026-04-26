variable "aws_region" {
  type        = string
  description = "AWS region for AltData Reliability OS."
  default     = "ap-south-1"
}

variable "project_name" {
  type        = string
  description = "Project name used for resource prefixes."
  default     = "altdata-reliability-os"
}

