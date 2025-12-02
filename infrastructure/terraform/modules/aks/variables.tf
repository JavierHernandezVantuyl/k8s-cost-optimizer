# AKS Module Variables

variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
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

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "availability_zones" {
  description = "Availability zones for node pools"
  type        = list(string)
  default     = ["1", "2", "3"]
}

# Network Configuration
variable "vnet_address_space" {
  description = "Address space for VNet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aks_subnet_cidr" {
  description = "CIDR for AKS subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "postgres_subnet_cidr" {
  description = "CIDR for PostgreSQL subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "service_cidr" {
  description = "CIDR for Kubernetes services"
  type        = string
  default     = "10.1.0.0/16"
}

variable "dns_service_ip" {
  description = "IP address for DNS service"
  type        = string
  default     = "10.1.0.10"
}

variable "docker_bridge_cidr" {
  description = "CIDR for Docker bridge"
  type        = string
  default     = "172.17.0.1/16"
}

# System Node Pool
variable "system_node_vm_size" {
  description = "VM size for system nodes"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "system_node_count" {
  description = "Initial count of system nodes"
  type        = number
  default     = 2
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
variable "app_node_vm_size" {
  description = "VM size for application nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "app_node_count" {
  description = "Initial count of application nodes"
  type        = number
  default     = 3
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

variable "app_node_spot_enabled" {
  description = "Enable spot instances for application nodes"
  type        = bool
  default     = false
}

variable "app_node_spot_max_price" {
  description = "Maximum price for spot instances (-1 for on-demand price)"
  type        = number
  default     = -1
}

# Security Configuration
variable "enable_network_policy" {
  description = "Enable network policy"
  type        = bool
  default     = true
}

variable "enable_azure_policy" {
  description = "Enable Azure Policy"
  type        = bool
  default     = false
}

variable "aad_admin_group_object_ids" {
  description = "AAD group object IDs for cluster admins"
  type        = list(string)
  default     = []
}

# Database Configuration
variable "db_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "optimizer"
  sensitive   = true
}

variable "db_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "db_sku_name" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "db_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768
}

# Redis Configuration
variable "redis_sku_name" {
  description = "Redis SKU name (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "redis_family" {
  description = "Redis family (C for Basic/Standard, P for Premium)"
  type        = string
  default     = "C"
}

variable "redis_capacity" {
  description = "Redis capacity (0-6 for Basic/Standard, 1-5 for Premium)"
  type        = number
  default     = 0
}
