# Development Environment Configuration
# Creates optimizer deployment on existing K8s cluster

terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    # Configure your backend here
    # bucket = "your-terraform-state-bucket"
    # key    = "k8s-cost-optimizer/dev/terraform.tfstate"
    # region = "us-east-1"
  }
}

# Configure providers
provider "kubernetes" {
  config_path = var.kubeconfig_path
}

# Deploy optimizer to existing cluster
module "optimizer" {
  source = "../../modules/optimizer"

  namespace   = "cost-optimizer-dev"
  environment = "dev"
  cost_center = var.cost_center

  # Database configuration (using local PostgreSQL or managed service)
  postgres_host     = var.postgres_host
  postgres_port     = var.postgres_port
  postgres_database = var.postgres_database
  postgres_username = var.postgres_username
  postgres_password = var.postgres_password

  # Redis configuration
  redis_host     = var.redis_host
  redis_port     = var.redis_port
  redis_password = var.redis_password

  # Storage configuration
  storage_endpoint   = var.storage_endpoint
  storage_access_key = var.storage_access_key
  storage_secret_key = var.storage_secret_key
  storage_bucket     = var.storage_bucket

  # Application configuration
  log_level                 = "DEBUG"
  metrics_enabled           = true
  analysis_interval         = "1h"
  min_confidence_threshold  = 0.6
  enable_auto_apply         = false
  dry_run_mode              = true
  cloud_providers           = ["aws", "gcp", "azure"]

  # Deployment configuration
  api_image               = var.api_image
  api_image_tag           = var.api_image_tag
  api_replicas            = 1
  api_resources_requests_cpu    = "100m"
  api_resources_requests_memory = "256Mi"
  api_resources_limits_cpu      = "500m"
  api_resources_limits_memory   = "1Gi"

  dashboard_image               = var.dashboard_image
  dashboard_image_tag           = var.dashboard_image_tag
  dashboard_replicas            = 1
  dashboard_resources_requests_cpu    = "50m"
  dashboard_resources_requests_memory = "128Mi"
  dashboard_resources_limits_cpu      = "250m"
  dashboard_resources_limits_memory   = "256Mi"

  # Service configuration
  service_type        = "ClusterIP"
  enable_ingress      = true
  ingress_class       = "nginx"
  enable_tls          = false
  domain_name         = "optimizer-dev.example.com"

  # Autoscaling
  enable_hpa               = false
  enable_network_policy    = false

  common_labels = {
    project     = "k8s-cost-optimizer"
    environment = "dev"
    managed_by  = "terraform"
  }
}
