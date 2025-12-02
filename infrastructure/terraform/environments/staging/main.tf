# Staging Environment Configuration

terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    # Configure your backend here
    # bucket = "your-terraform-state-bucket"
    # key    = "k8s-cost-optimizer/staging/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

module "optimizer" {
  source = "../../modules/optimizer"

  namespace   = "cost-optimizer-staging"
  environment = "staging"
  cost_center = var.cost_center

  postgres_host     = var.postgres_host
  postgres_port     = var.postgres_port
  postgres_database = var.postgres_database
  postgres_username = var.postgres_username
  postgres_password = var.postgres_password

  redis_host     = var.redis_host
  redis_port     = var.redis_port
  redis_password = var.redis_password

  storage_endpoint   = var.storage_endpoint
  storage_access_key = var.storage_access_key
  storage_secret_key = var.storage_secret_key
  storage_bucket     = var.storage_bucket

  log_level                = "INFO"
  metrics_enabled          = true
  analysis_interval        = "3h"
  min_confidence_threshold = 0.7
  enable_auto_apply        = false
  dry_run_mode             = true
  cloud_providers          = ["aws", "gcp", "azure"]

  api_image                     = var.api_image
  api_image_tag                 = var.api_image_tag
  api_replicas                  = 2
  api_resources_requests_cpu    = "250m"
  api_resources_requests_memory = "512Mi"
  api_resources_limits_cpu      = "1000m"
  api_resources_limits_memory   = "2Gi"

  dashboard_image                     = var.dashboard_image
  dashboard_image_tag                 = var.dashboard_image_tag
  dashboard_replicas                  = 2
  dashboard_resources_requests_cpu    = "100m"
  dashboard_resources_requests_memory = "128Mi"
  dashboard_resources_limits_cpu      = "500m"
  dashboard_resources_limits_memory   = "512Mi"

  service_type   = "ClusterIP"
  enable_ingress = true
  ingress_class  = "nginx"
  enable_tls     = true
  domain_name    = "optimizer-staging.example.com"

  enable_hpa            = true
  hpa_min_replicas      = 2
  hpa_max_replicas      = 5
  enable_network_policy = false

  common_labels = {
    project     = "k8s-cost-optimizer"
    environment = "staging"
    managed_by  = "terraform"
  }
}
