variable "region" {
  type    = string
  default = "us-east-1"
}

variable "ami" {
  description = "Optional custom AMI ID. Leave empty to auto-pick latest Amazon Linux 2023 in the selected region."
  type        = string
  default     = ""
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "ssh_key_name" {
  description = "Name of an existing AWS EC2 key pair to access the instance"
  type        = string
  default     = "cloud"
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks that can SSH to app instances"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "excluded_availability_zones" {
  description = "Availability zones to exclude from ASG and ALB subnets."
  type        = list(string)
  default     = ["us-east-1e"]
}

variable "repo_url" {
  description = "Git repository URL used by EC2 bootstrap script"
  type        = string
  default     = "https://github.com/FEILI13/cloud.git"
}

variable "repo_subdir" {
  description = "Subdirectory containing Dockerfile in the repository. Leave empty if Dockerfile is at repo root."
  type        = string
  default     = "cloud_app"
}

variable "asg_min_size" {
  type    = number
  default = 2
}

variable "asg_max_size" {
  type    = number
  default = 4
}

variable "asg_desired_capacity" {
  type    = number
  default = 2
}

variable "db_name" {
  type    = string
  default = "ageoverflow"
}

variable "db_username" {
  type    = string
  default = "ageoverflow"
}

variable "db_password" {
  description = "RDS PostgreSQL password. Change this in terraform.tfvars for production."
  type        = string
  sensitive   = true
  default     = "Ageoverflow123!"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}
