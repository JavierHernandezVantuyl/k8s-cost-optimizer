# Optimizer Module Variables

# General Configuration
variable "namespace" {
  description = "Kubernetes namespace for optimizer deployment"
  type        = string
  default     = "cost-optimizer"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "cost_center" {
  description = "Cost center for billing and tagging"
  type        = string
  default     = "infrastructure"
}

variable "common_labels" {
  description = "Common labels to apply to all resources"
  type        = map(string)
  default     = {}
}

# Database Configuration
variable "postgres_host" {
  description = "PostgreSQL host address"
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

# Redis Configuration
variable "redis_host" {
  description = "Redis host address"
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

# Storage Configuration
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
  default     = "optimizer-data"
}

# Application Configuration
variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL."
  }
}

variable "metrics_enabled" {
  description = "Enable Prometheus metrics"
  type        = bool
  default     = true
}

variable "metrics_port" {
  description = "Metrics port"
  type        = number
  default     = 9090
}

variable "analysis_interval" {
  description = "Interval for cost analysis (e.g., 1h, 6h, 24h)"
  type        = string
  default     = "6h"
}

variable "min_confidence_threshold" {
  description = "Minimum confidence threshold for recommendations (0.0-1.0)"
  type        = number
  default     = 0.7
  validation {
    condition     = var.min_confidence_threshold >= 0.0 && var.min_confidence_threshold <= 1.0
    error_message = "Confidence threshold must be between 0.0 and 1.0."
  }
}

variable "enable_auto_apply" {
  description = "Enable automatic application of recommendations"
  type        = bool
  default     = false
}

variable "dry_run_mode" {
  description = "Run in dry-run mode (no actual modifications)"
  type        = bool
  default     = true
}

variable "cloud_providers" {
  description = "List of cloud providers to monitor (aws, gcp, azure)"
  type        = list(string)
  default     = ["aws", "gcp", "azure"]
}

# API Deployment Configuration
variable "api_image" {
  description = "Optimizer API container image"
  type        = string
  default     = "k8s-cost-optimizer/api"
}

variable "api_image_tag" {
  description = "Optimizer API image tag"
  type        = string
  default     = "latest"
}

variable "api_replicas" {
  description = "Number of API replicas"
  type        = number
  default     = 2
  validation {
    condition     = var.api_replicas >= 1 && var.api_replicas <= 10
    error_message = "API replicas must be between 1 and 10."
  }
}

variable "api_resources_requests_cpu" {
  description = "API CPU requests"
  type        = string
  default     = "250m"
}

variable "api_resources_requests_memory" {
  description = "API memory requests"
  type        = string
  default     = "512Mi"
}

variable "api_resources_limits_cpu" {
  description = "API CPU limits"
  type        = string
  default     = "1000m"
}

variable "api_resources_limits_memory" {
  description = "API memory limits"
  type        = string
  default     = "2Gi"
}

# Dashboard Configuration
variable "dashboard_image" {
  description = "Dashboard container image"
  type        = string
  default     = "k8s-cost-optimizer/dashboard"
}

variable "dashboard_image_tag" {
  description = "Dashboard image tag"
  type        = string
  default     = "latest"
}

variable "dashboard_replicas" {
  description = "Number of dashboard replicas"
  type        = number
  default     = 2
}

variable "dashboard_resources_requests_cpu" {
  description = "Dashboard CPU requests"
  type        = string
  default     = "100m"
}

variable "dashboard_resources_requests_memory" {
  description = "Dashboard memory requests"
  type        = string
  default     = "128Mi"
}

variable "dashboard_resources_limits_cpu" {
  description = "Dashboard CPU limits"
  type        = string
  default     = "500m"
}

variable "dashboard_resources_limits_memory" {
  description = "Dashboard memory limits"
  type        = string
  default     = "512Mi"
}

# Service Configuration
variable "service_type" {
  description = "Kubernetes service type"
  type        = string
  default     = "ClusterIP"
  validation {
    condition     = contains(["ClusterIP", "NodePort", "LoadBalancer"], var.service_type)
    error_message = "Service type must be ClusterIP, NodePort, or LoadBalancer."
  }
}

variable "service_annotations" {
  description = "Annotations for services"
  type        = map(string)
  default     = {}
}

# Ingress Configuration
variable "enable_ingress" {
  description = "Enable ingress for external access"
  type        = bool
  default     = false
}

variable "ingress_class" {
  description = "Ingress class name"
  type        = string
  default     = "nginx"
}

variable "ingress_annotations" {
  description = "Additional ingress annotations"
  type        = map(string)
  default     = {}
}

variable "enable_tls" {
  description = "Enable TLS for ingress"
  type        = bool
  default     = true
}

variable "cert_manager_issuer" {
  description = "Cert-manager ClusterIssuer name"
  type        = string
  default     = "letsencrypt-prod"
}

variable "domain_name" {
  description = "Domain name for ingress"
  type        = string
  default     = "optimizer.example.com"
}

# Autoscaling Configuration
variable "enable_hpa" {
  description = "Enable Horizontal Pod Autoscaler"
  type        = bool
  default     = true
}

variable "hpa_min_replicas" {
  description = "Minimum replicas for HPA"
  type        = number
  default     = 2
}

variable "hpa_max_replicas" {
  description = "Maximum replicas for HPA"
  type        = number
  default     = 10
}

variable "hpa_target_cpu_utilization" {
  description = "Target CPU utilization percentage for HPA"
  type        = number
  default     = 70
}

variable "hpa_target_memory_utilization" {
  description = "Target memory utilization percentage for HPA"
  type        = number
  default     = 80
}

# Security Configuration
variable "service_account_annotations" {
  description = "Annotations for service account (e.g., IAM role)"
  type        = map(string)
  default     = {}
}

variable "aws_iam_role_arn" {
  description = "AWS IAM role ARN for service account (IRSA)"
  type        = string
  default     = ""
}

variable "image_pull_secret_name" {
  description = "Name of image pull secret"
  type        = string
  default     = "regcred"
}

variable "image_pull_policy" {
  description = "Image pull policy"
  type        = string
  default     = "IfNotPresent"
  validation {
    condition     = contains(["Always", "IfNotPresent", "Never"], var.image_pull_policy)
    error_message = "Image pull policy must be Always, IfNotPresent, or Never."
  }
}

variable "enable_network_policy" {
  description = "Enable network policies for pod communication"
  type        = bool
  default     = false
}
