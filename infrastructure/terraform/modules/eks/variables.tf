# EKS Module Variables

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "infrastructure"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# Cluster Configuration
variable "cluster_endpoint_public_access" {
  description = "Enable public access to cluster endpoint"
  type        = bool
  default     = true
}

# System Node Group
variable "system_node_instance_types" {
  description = "Instance types for system node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "system_node_min_size" {
  description = "Minimum size of system node group"
  type        = number
  default     = 2
}

variable "system_node_max_size" {
  description = "Maximum size of system node group"
  type        = number
  default     = 4
}

variable "system_node_desired_size" {
  description = "Desired size of system node group"
  type        = number
  default     = 2
}

# Application Node Group
variable "app_node_instance_types" {
  description = "Instance types for application node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "app_node_capacity_type" {
  description = "Capacity type for application nodes (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"
}

variable "app_node_min_size" {
  description = "Minimum size of application node group"
  type        = number
  default     = 2
}

variable "app_node_max_size" {
  description = "Maximum size of application node group"
  type        = number
  default     = 10
}

variable "app_node_desired_size" {
  description = "Desired size of application node group"
  type        = number
  default     = 3
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Initial database storage (GB)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum database storage for autoscaling (GB)"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "Master username for database"
  type        = string
  default     = "optimizer"
  sensitive   = true
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

# S3 Configuration
variable "cost_optimizer_bucket" {
  description = "S3 bucket name for optimizer data"
  type        = string
}
