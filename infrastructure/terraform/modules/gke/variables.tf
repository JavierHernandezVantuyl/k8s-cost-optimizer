# GKE Module Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone (used for zonal clusters)"
  type        = string
  default     = "us-central1-a"
}

variable "regional_cluster" {
  description = "Create a regional cluster"
  type        = bool
  default     = true
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

variable "common_labels" {
  description = "Common labels for all resources"
  type        = map(string)
  default     = {}
}

# Network Configuration
variable "subnet_cidr" {
  description = "CIDR range for subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "pods_cidr" {
  description = "CIDR range for pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR range for services"
  type        = string
  default     = "10.2.0.0/16"
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for GKE master"
  type        = string
  default     = "172.16.0.0/28"
}

variable "enable_private_nodes" {
  description = "Enable private nodes"
  type        = bool
  default     = true
}

variable "enable_private_endpoint" {
  description = "Enable private endpoint"
  type        = bool
  default     = false
}

variable "master_authorized_networks" {
  description = "List of master authorized networks"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}

# Cluster Configuration
variable "release_channel" {
  description = "Release channel (RAPID, REGULAR, STABLE)"
  type        = string
  default     = "REGULAR"
}

variable "enable_network_policy" {
  description = "Enable network policy"
  type        = bool
  default     = true
}

variable "enable_binary_authorization" {
  description = "Enable binary authorization"
  type        = bool
  default     = false
}

variable "enable_vertical_pod_autoscaling" {
  description = "Enable vertical pod autoscaling"
  type        = bool
  default     = true
}

variable "enable_cluster_autoscaling" {
  description = "Enable cluster autoscaling"
  type        = bool
  default     = false
}

variable "enable_managed_prometheus" {
  description = "Enable managed Prometheus"
  type        = bool
  default     = true
}

# System Node Pool
variable "system_node_machine_type" {
  description = "Machine type for system nodes"
  type        = string
  default     = "e2-medium"
}

variable "system_node_count" {
  description = "Number of system nodes (zonal cluster)"
  type        = number
  default     = 2
}

variable "system_node_count_per_zone" {
  description = "Number of system nodes per zone (regional cluster)"
  type        = number
  default     = 1
}

variable "system_node_min_count" {
  description = "Minimum system node count"
  type        = number
  default     = 2
}

variable "system_node_max_count" {
  description = "Maximum system node count"
  type        = number
  default     = 4
}

# Application Node Pool
variable "app_node_machine_type" {
  description = "Machine type for application nodes"
  type        = string
  default     = "e2-standard-2"
}

variable "app_node_preemptible" {
  description = "Use preemptible instances for application nodes"
  type        = bool
  default     = false
}

variable "app_node_count" {
  description = "Number of application nodes (zonal cluster)"
  type        = number
  default     = 3
}

variable "app_node_count_per_zone" {
  description = "Number of application nodes per zone (regional cluster)"
  type        = number
  default     = 1
}

variable "app_node_min_count" {
  description = "Minimum application node count"
  type        = number
  default     = 2
}

variable "app_node_max_count" {
  description = "Maximum application node count"
  type        = number
  default     = 10
}

# Database Configuration
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 20
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "optimizer"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Redis Configuration
variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# Storage Configuration
variable "optimizer_bucket_name" {
  description = "GCS bucket name for optimizer data"
  type        = string
}
