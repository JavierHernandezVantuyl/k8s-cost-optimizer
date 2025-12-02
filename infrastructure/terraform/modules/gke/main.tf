# GKE Cluster Module for K8s Cost Optimizer
# Creates production-ready GKE cluster with all necessary features

terraform {
  required_version = ">= 1.5.0"
}

data "google_client_config" "default" {}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.cluster_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
}

# Cloud Router for NAT
resource "google_compute_router" "router" {
  name    = "${var.cluster_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.project_id
}

# Cloud NAT
resource "google_compute_router_nat" "nat" {
  name                               = "${var.cluster_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  project                            = var.project_id

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.regional_cluster ? var.region : var.zone
  project  = var.project_id

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  # IP allocation policy for VPC-native cluster
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Network policy
  network_policy {
    enabled  = var.enable_network_policy
    provider = var.enable_network_policy ? "PROVIDER_UNSPECIFIED" : null
  }

  # Master auth
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = var.enable_private_nodes
    enable_private_endpoint = var.enable_private_endpoint
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  # Master authorized networks
  dynamic "master_authorized_networks_config" {
    for_each = length(var.master_authorized_networks) > 0 ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Maintenance policy
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  # Release channel
  release_channel {
    channel = var.release_channel
  }

  # Binary authorization
  binary_authorization {
    evaluation_mode = var.enable_binary_authorization ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }

  # Enable vertical pod autoscaling
  vertical_pod_autoscaling {
    enabled = var.enable_vertical_pod_autoscaling
  }

  # Cluster autoscaling
  cluster_autoscaling {
    enabled = var.enable_cluster_autoscaling
    dynamic "auto_provisioning_defaults" {
      for_each = var.enable_cluster_autoscaling ? [1] : []
      content {
        service_account = google_service_account.cluster_nodes.email
        oauth_scopes = [
          "https://www.googleapis.com/auth/cloud-platform"
        ]
      }
    }
  }

  # Monitoring and logging
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
    managed_prometheus {
      enabled = var.enable_managed_prometheus
    }
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = !var.enable_network_policy
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  resource_labels = merge(
    var.common_labels,
    {
      environment = var.environment
      cost_center = var.cost_center
      managed_by  = "terraform"
    }
  )
}

# Service Account for Cluster Nodes
resource "google_service_account" "cluster_nodes" {
  account_id   = "${var.cluster_name}-nodes"
  display_name = "Service Account for ${var.cluster_name} GKE nodes"
  project      = var.project_id
}

# IAM bindings for node service account
resource "google_project_iam_member" "node_service_account_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cluster_nodes.email}"
}

resource "google_project_iam_member" "node_service_account_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cluster_nodes.email}"
}

resource "google_project_iam_member" "node_service_account_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.cluster_nodes.email}"
}

# System Node Pool
resource "google_container_node_pool" "system" {
  name       = "system-pool"
  location   = google_container_cluster.primary.location
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  node_count = var.regional_cluster ? var.system_node_count_per_zone : var.system_node_count

  autoscaling {
    min_node_count = var.system_node_min_count
    max_node_count = var.system_node_max_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type    = var.system_node_machine_type
    service_account = google_service_account.cluster_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = merge(
      var.common_labels,
      {
        role        = "system"
        environment = var.environment
        cost_center = var.cost_center
      }
    )

    tags = ["gke-node", "${var.cluster_name}-node", "system"]

    disk_size_gb = 100
    disk_type    = "pd-standard"
    image_type   = "COS_CONTAINERD"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
}

# Application Node Pool
resource "google_container_node_pool" "application" {
  name       = "application-pool"
  location   = google_container_cluster.primary.location
  cluster    = google_container_cluster.primary.name
  project    = var.project_id
  node_count = var.regional_cluster ? var.app_node_count_per_zone : var.app_node_count

  autoscaling {
    min_node_count = var.app_node_min_count
    max_node_count = var.app_node_max_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type    = var.app_node_machine_type
    preemptible     = var.app_node_preemptible
    service_account = google_service_account.cluster_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = merge(
      var.common_labels,
      {
        role        = "application"
        environment = var.environment
        cost_center = var.cost_center
      }
    )

    tags = ["gke-node", "${var.cluster_name}-node", "application"]

    disk_size_gb = 100
    disk_type    = "pd-standard"
    image_type   = "COS_CONTAINERD"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "${var.cluster_name}-db"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = var.db_disk_size
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "prod"
      start_time                     = "03:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 30 : 7
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }

    user_labels = merge(
      var.common_labels,
      {
        environment = var.environment
        cost_center = var.cost_center
      }
    )
  }

  deletion_protection = var.environment == "prod"
}

# Cloud SQL Database
resource "google_sql_database" "database" {
  name     = "k8s_optimizer"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

# Cloud SQL User
resource "google_sql_user" "user" {
  name     = var.db_username
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
  project  = var.project_id
}

# Memorystore Redis Instance
resource "google_redis_instance" "redis" {
  name               = "${var.cluster_name}-redis"
  tier               = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = var.redis_memory_size_gb
  region             = var.region
  redis_version      = "REDIS_7_0"
  authorized_network = google_compute_network.vpc.id
  project            = var.project_id

  display_name = "Redis for K8s Cost Optimizer"

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }

  labels = merge(
    var.common_labels,
    {
      environment = var.environment
      cost_center = var.cost_center
    }
  )
}

# GCS Bucket for Optimizer Data
resource "google_storage_bucket" "optimizer_data" {
  name          = var.optimizer_bucket_name
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 90 : 30
    }
    action {
      type = "Delete"
    }
  }

  labels = merge(
    var.common_labels,
    {
      environment = var.environment
      cost_center = var.cost_center
    }
  )
}

# Service Account for Cost Optimizer
resource "google_service_account" "cost_optimizer" {
  account_id   = "${var.cluster_name}-optimizer"
  display_name = "Service Account for Cost Optimizer"
  project      = var.project_id
}

# IAM bindings for cost optimizer
resource "google_project_iam_member" "cost_optimizer_compute_viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  member  = "serviceAccount:${google_service_account.cost_optimizer.email}"
}

resource "google_project_iam_member" "cost_optimizer_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.cost_optimizer.email}"
}

resource "google_storage_bucket_iam_member" "cost_optimizer_storage_admin" {
  bucket = google_storage_bucket.optimizer_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cost_optimizer.email}"
}

# Workload Identity binding
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.cost_optimizer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[cost-optimizer/optimizer-sa]"
}
