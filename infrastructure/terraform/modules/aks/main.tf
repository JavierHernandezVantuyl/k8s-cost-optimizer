# AKS Cluster Module for K8s Cost Optimizer
# Creates production-ready AKS cluster with all necessary features

terraform {
  required_version = ">= 1.5.0"
}

data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.cluster_name}-rg"
  location = var.location

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
      ManagedBy   = "terraform"
    }
  )
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "${var.cluster_name}-vnet"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = [var.vnet_address_space]

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  )
}

# Subnet for AKS
resource "azurerm_subnet" "aks" {
  name                 = "${var.cluster_name}-aks-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.aks_subnet_cidr]
}

# Subnet for PostgreSQL
resource "azurerm_subnet" "postgres" {
  name                 = "${var.cluster_name}-postgres-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.postgres_subnet_cidr]

  delegation {
    name = "fs"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# User Assigned Identity for AKS
resource "azurerm_user_assigned_identity" "aks" {
  name                = "${var.cluster_name}-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(
    var.common_tags,
    {
      CostCenter = var.cost_center
    }
  )
}

# Role assignment for AKS to manage network resources
resource "azurerm_role_assignment" "aks_network_contributor" {
  scope                = azurerm_virtual_network.main.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks.principal_id
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.cluster_name}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  )
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = var.cluster_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  # Default system node pool
  default_node_pool {
    name                = "system"
    vm_size             = var.system_node_vm_size
    enable_auto_scaling = true
    min_count           = var.system_node_min_count
    max_count           = var.system_node_max_count
    node_count          = var.system_node_count
    vnet_subnet_id      = azurerm_subnet.aks.id
    type                = "VirtualMachineScaleSets"
    zones               = var.availability_zones

    node_labels = {
      role = "system"
    }

    tags = merge(
      var.common_tags,
      {
        NodePool   = "system"
        CostCenter = var.cost_center
      }
    )
  }

  # Identity
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks.id]
  }

  # Network profile
  network_profile {
    network_plugin     = "azure"
    network_policy     = var.enable_network_policy ? "azure" : null
    load_balancer_sku  = "standard"
    outbound_type      = "loadBalancer"
    dns_service_ip     = var.dns_service_ip
    service_cidr       = var.service_cidr
    docker_bridge_cidr = var.docker_bridge_cidr
  }

  # Azure Active Directory integration
  azure_active_directory_role_based_access_control {
    managed                = true
    admin_group_object_ids = var.aad_admin_group_object_ids
    azure_rbac_enabled     = true
  }

  # Workload identity (for OIDC)
  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  # Monitoring
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  azure_policy_enabled = var.enable_azure_policy

  # Auto-scaler profile
  auto_scaler_profile {
    balance_similar_node_groups      = true
    expander                         = "random"
    max_graceful_termination_sec     = 600
    max_node_provisioning_time       = "15m"
    max_unready_nodes                = 3
    max_unready_percentage           = 45
    new_pod_scale_up_delay           = "10s"
    scale_down_delay_after_add       = "10m"
    scale_down_delay_after_delete    = "10s"
    scale_down_delay_after_failure   = "3m"
    scan_interval                    = "10s"
    scale_down_unneeded              = "10m"
    scale_down_unready               = "20m"
    scale_down_utilization_threshold = "0.5"
  }

  # Maintenance window
  maintenance_window {
    allowed {
      day   = "Sunday"
      hours = [0, 1, 2, 3]
    }
  }

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  )

  depends_on = [
    azurerm_role_assignment.aks_network_contributor
  ]
}

# Application Node Pool
resource "azurerm_kubernetes_cluster_node_pool" "application" {
  name                  = "application"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.app_node_vm_size
  enable_auto_scaling   = true
  min_count             = var.app_node_min_count
  max_count             = var.app_node_max_count
  node_count            = var.app_node_count
  vnet_subnet_id        = azurerm_subnet.aks.id
  zones                 = var.availability_zones
  priority              = var.app_node_spot_enabled ? "Spot" : "Regular"
  eviction_policy       = var.app_node_spot_enabled ? "Delete" : null
  spot_max_price        = var.app_node_spot_enabled ? var.app_node_spot_max_price : null

  node_labels = {
    role = "application"
  }

  tags = merge(
    var.common_tags,
    {
      NodePool   = "application"
      CostCenter = var.cost_center
    }
  )
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.cluster_name}-postgres"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15"
  delegated_subnet_id    = azurerm_subnet.postgres.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  administrator_login    = var.db_admin_username
  administrator_password = var.db_admin_password
  zone                   = "1"

  storage_mb   = var.db_storage_mb
  sku_name     = var.db_sku_name
  backup_retention_days = var.environment == "prod" ? 30 : 7

  high_availability {
    mode                      = var.environment == "prod" ? "ZoneRedundant" : "Disabled"
    standby_availability_zone = var.environment == "prod" ? "2" : null
  }

  maintenance_window {
    day_of_week  = 0
    start_hour   = 3
    start_minute = 0
  }

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  )

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "k8s_optimizer"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

# Private DNS Zone for PostgreSQL
resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.cluster_name}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(
    var.common_tags,
    {
      CostCenter = var.cost_center
    }
  )
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.cluster_name}-postgres-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
  resource_group_name   = azurerm_resource_group.main.name

  tags = merge(
    var.common_tags,
    {
      CostCenter = var.cost_center
    }
  )
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "main" {
  name                = "${var.cluster_name}-redis"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.redis_capacity
  family              = var.redis_family
  sku_name            = var.redis_sku_name
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    enable_authentication = true
  }

  zones = var.environment == "prod" ? var.availability_zones : null

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  )
}

# Storage Account for Optimizer Data
resource "azurerm_storage_account" "optimizer" {
  name                     = replace("${var.cluster_name}storage", "-", "")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = var.environment == "prod" ? "GRS" : "LRS"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = var.environment == "prod" ? 30 : 7
    }
  }

  tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      CostCenter  = var.cost_center
    }
  )
}

resource "azurerm_storage_container" "optimizer_data" {
  name                  = "optimizer-data"
  storage_account_name  = azurerm_storage_account.optimizer.name
  container_access_type = "private"
}

# User Assigned Identity for Cost Optimizer
resource "azurerm_user_assigned_identity" "cost_optimizer" {
  name                = "${var.cluster_name}-optimizer-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = merge(
    var.common_tags,
    {
      CostCenter = var.cost_center
    }
  )
}

# Role assignments for cost optimizer
resource "azurerm_role_assignment" "optimizer_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.optimizer.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.cost_optimizer.principal_id
}

resource "azurerm_role_assignment" "optimizer_reader" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.cost_optimizer.principal_id
}

resource "azurerm_role_assignment" "optimizer_monitoring_reader" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_user_assigned_identity.cost_optimizer.principal_id
}

# Federated Identity Credential for Workload Identity
resource "azurerm_federated_identity_credential" "cost_optimizer" {
  name                = "${var.cluster_name}-optimizer-federated-credential"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.cost_optimizer.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:cost-optimizer:optimizer-sa"
}
