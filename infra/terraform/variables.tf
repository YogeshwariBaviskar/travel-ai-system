variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "travel-ai"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "travel_ai_user"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Custom domain for the application"
  type        = string
  default     = ""
}
