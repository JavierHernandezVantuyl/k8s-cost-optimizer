# Optimizer Module Outputs

output "namespace" {
  description = "Namespace where optimizer is deployed"
  value       = kubernetes_namespace.optimizer.metadata[0].name
}

output "api_service_name" {
  description = "Name of the optimizer API service"
  value       = kubernetes_service.optimizer_api.metadata[0].name
}

output "api_service_endpoint" {
  description = "Internal endpoint for the optimizer API"
  value       = "${kubernetes_service.optimizer_api.metadata[0].name}.${kubernetes_namespace.optimizer.metadata[0].name}.svc.cluster.local:8000"
}

output "dashboard_service_name" {
  description = "Name of the dashboard service"
  value       = kubernetes_service.dashboard.metadata[0].name
}

output "dashboard_service_endpoint" {
  description = "Internal endpoint for the dashboard"
  value       = "${kubernetes_service.dashboard.metadata[0].name}.${kubernetes_namespace.optimizer.metadata[0].name}.svc.cluster.local"
}

output "ingress_hostname" {
  description = "Hostname for ingress (if enabled)"
  value       = var.enable_ingress ? var.domain_name : null
}

output "service_account_name" {
  description = "Name of the optimizer service account"
  value       = kubernetes_service_account.optimizer.metadata[0].name
}

output "api_deployment_name" {
  description = "Name of the API deployment"
  value       = kubernetes_deployment.optimizer_api.metadata[0].name
}

output "dashboard_deployment_name" {
  description = "Name of the dashboard deployment"
  value       = kubernetes_deployment.dashboard.metadata[0].name
}

output "postgres_secret_name" {
  description = "Name of the PostgreSQL credentials secret"
  value       = kubernetes_secret.postgres_credentials.metadata[0].name
}

output "redis_secret_name" {
  description = "Name of the Redis credentials secret"
  value       = kubernetes_secret.redis_credentials.metadata[0].name
}

output "storage_secret_name" {
  description = "Name of the storage credentials secret"
  value       = kubernetes_secret.storage_credentials.metadata[0].name
}

output "config_map_name" {
  description = "Name of the optimizer config map"
  value       = kubernetes_config_map.optimizer_config.metadata[0].name
}
