variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix applied to all resource names/tags."
  type        = string
  default     = "notif"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets (one per AZ)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "github_repo_url" {
  description = "Git URL the EC2 instances clone to get the app code."
  type        = string
  default     = "https://github.com/mohammadadil17/Real-Time-Notification-System.git"
}

variable "github_repo_branch" {
  description = "Branch to check out on the EC2 instances."
  type        = string
  default     = "main"
}

variable "data_instance_type" {
  description = "Instance type for the single data-tier instance (Postgres + Redis + Kafka). Not part of the ASG: it holds state, so it isn't horizontally scaled. t3.small (2GB RAM) rather than t3.micro because Kafka's JVM heap alone can be tight on 1GB."
  type        = string
  default     = "t3.small"
}

variable "app_instance_type" {
  description = "Instance type for the stateless app-tier ASG (FastAPI app + consumer + digest-worker)."
  type        = string
  default     = "t3.micro"
}

variable "app_asg_min_size" {
  type    = number
  default = 1
}

variable "app_asg_max_size" {
  type    = number
  default = 3
}

variable "app_asg_desired_capacity" {
  type    = number
  default = 1
}

variable "app_cpu_target" {
  description = "Target average CPU utilization (%) the Auto Scaling Group's scaling policy tries to maintain."
  type        = number
  default     = 50
}

variable "jwt_secret_key" {
  description = "Secret used to sign JWTs in production. Required, no default: the local dev placeholder must never be reused here. Pass via terraform.tfvars (gitignored) or TF_VAR_jwt_secret_key so it never lands in version control."
  type        = string
  sensitive   = true
}
