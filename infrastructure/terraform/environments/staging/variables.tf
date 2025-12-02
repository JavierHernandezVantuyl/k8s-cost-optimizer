# Staging Environment Variables

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "infrastructure"
}

variable "postgres_host" {
  description = "PostgreSQL host"
  type        = string
}

variable "postgres_port" {
  description = "PostgreSQL port"
  type        = number
  default     = 5432
}

variable "postgres_database" {
  description = "PostgreSQL database name"
  type        = string
  default     = "k8s_optimizer"
}

variable "postgres_username" {
  description = "PostgreSQL username"
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "redis_host" {
  description = "Redis host"
  type        = string
}

variable "redis_port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "storage_endpoint" {
  description = "S3-compatible storage endpoint"
  type        = string
}

variable "storage_access_key" {
  description = "Storage access key"
  type        = string
  sensitive   = true
}

variable "storage_secret_key" {
  description = "Storage secret key"
  type        = string
  sensitive   = true
}

variable "storage_bucket" {
  description = "Storage bucket name"
  type        = string
  default     = "optimizer-staging-data"
}

variable "api_image" {
  description = "API container image"
  type        = string
  default     = "your-registry/k8s-cost-optimizer-api"
}

variable "api_image_tag" {
  description = "API image tag"
  type        = string
  default     = "staging"
}

variable "dashboard_image" {
  description = "Dashboard container image"
  type        = string
  default     = "your-registry/k8s-cost-optimizer-dashboard"
}

variable "dashboard_image_tag" {
  description = "Dashboard image tag"
  type        = string
  default     = "staging"
}
