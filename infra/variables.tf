variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the main VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "db_username" {
  description = "Postgres master username"
  type        = string
  default     = "jaelyn"
}

variable "db_password" {
  description = "Postgres master password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Name of the Postgres database"
  type        = string
  default     = "quant"
}

variable "api_key" {
  description = "Your Polygon API key (used by ingestion & backtester)"
  type        = string
  default     = "XbTx7h_kP0dGxI8fdRCC7Blx9i0Wjr3l"
}
