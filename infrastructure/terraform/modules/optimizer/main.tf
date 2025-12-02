# Optimizer Module - Core Application Resources
# Deploys the K8s Cost Optimizer to any Kubernetes cluster

terraform {
  required_version = ">= 1.5.0"
}

# Kubernetes Namespace
resource "kubernetes_namespace" "optimizer" {
  metadata {
    name = var.namespace
    labels = merge(
      var.common_labels,
      {
        app                       = "k8s-cost-optimizer"
        environment               = var.environment
        "cost-center"             = var.cost_center
        "managed-by"              = "terraform"
      }
    )
  }
}

# PostgreSQL Database (using cloud provider's managed service)
resource "kubernetes_secret" "postgres_credentials" {
  metadata {
    name      = "postgres-credentials"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
  }

  data = {
    host     = var.postgres_host
    port     = tostring(var.postgres_port)
    database = var.postgres_database
    username = var.postgres_username
    password = var.postgres_password
  }

  type = "Opaque"
}

# Redis Credentials
resource "kubernetes_secret" "redis_credentials" {
  metadata {
    name      = "redis-credentials"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
  }

  data = {
    host     = var.redis_host
    port     = tostring(var.redis_port)
    password = var.redis_password
  }

  type = "Opaque"
}

# MinIO/S3 Credentials
resource "kubernetes_secret" "storage_credentials" {
  metadata {
    name      = "storage-credentials"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
  }

  data = {
    endpoint   = var.storage_endpoint
    access_key = var.storage_access_key
    secret_key = var.storage_secret_key
    bucket     = var.storage_bucket
  }

  type = "Opaque"
}

# ConfigMap for Application Configuration
resource "kubernetes_config_map" "optimizer_config" {
  metadata {
    name      = "optimizer-config"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels = merge(
      var.common_labels,
      {
        app = "k8s-cost-optimizer"
      }
    )
  }

  data = {
    LOG_LEVEL           = var.log_level
    METRICS_ENABLED     = tostring(var.metrics_enabled)
    METRICS_PORT        = tostring(var.metrics_port)
    ANALYSIS_INTERVAL   = var.analysis_interval
    MIN_CONFIDENCE      = tostring(var.min_confidence_threshold)
    ENABLE_AUTO_APPLY   = tostring(var.enable_auto_apply)
    DRY_RUN_MODE        = tostring(var.dry_run_mode)
    CLOUD_PROVIDERS     = join(",", var.cloud_providers)
  }
}

# Service Account for Optimizer
resource "kubernetes_service_account" "optimizer" {
  metadata {
    name      = "optimizer-sa"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    annotations = merge(
      var.service_account_annotations,
      {
        "eks.amazonaws.com/role-arn" = var.aws_iam_role_arn
      }
    )
    labels = var.common_labels
  }

  automount_service_account_token = true
}

# ClusterRole for reading cluster resources
resource "kubernetes_cluster_role" "optimizer_reader" {
  metadata {
    name = "${var.namespace}-optimizer-reader"
    labels = var.common_labels
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "nodes", "persistentvolumeclaims", "services", "namespaces"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "statefulsets", "daemonsets", "replicasets"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["batch"]
    resources  = ["jobs", "cronjobs"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["metrics.k8s.io"]
    resources  = ["pods", "nodes"]
    verbs      = ["get", "list"]
  }

  rule {
    api_groups = ["autoscaling"]
    resources  = ["horizontalpodautoscalers"]
    verbs      = ["get", "list", "watch"]
  }
}

# ClusterRoleBinding
resource "kubernetes_cluster_role_binding" "optimizer_reader" {
  metadata {
    name = "${var.namespace}-optimizer-reader-binding"
    labels = var.common_labels
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.optimizer_reader.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.optimizer.metadata[0].name
    namespace = kubernetes_namespace.optimizer.metadata[0].name
  }
}

# Role for modifying resources (if auto-apply is enabled)
resource "kubernetes_role" "optimizer_modifier" {
  count = var.enable_auto_apply ? 1 : 0

  metadata {
    name      = "optimizer-modifier"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels    = var.common_labels
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "statefulsets"]
    verbs      = ["get", "list", "watch", "patch", "update"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch", "delete"]
  }

  rule {
    api_groups = ["autoscaling"]
    resources  = ["horizontalpodautoscalers"]
    verbs      = ["get", "list", "watch", "create", "patch", "update"]
  }
}

# RoleBinding for modification permissions
resource "kubernetes_role_binding" "optimizer_modifier" {
  count = var.enable_auto_apply ? 1 : 0

  metadata {
    name      = "optimizer-modifier-binding"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels    = var.common_labels
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.optimizer_modifier[0].metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.optimizer.metadata[0].name
    namespace = kubernetes_namespace.optimizer.metadata[0].name
  }
}

# Optimizer API Deployment
resource "kubernetes_deployment" "optimizer_api" {
  metadata {
    name      = "optimizer-api"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels = merge(
      var.common_labels,
      {
        app       = "optimizer-api"
        component = "backend"
      }
    )
  }

  spec {
    replicas = var.api_replicas

    selector {
      match_labels = {
        app       = "optimizer-api"
        component = "backend"
      }
    }

    template {
      metadata {
        labels = merge(
          var.common_labels,
          {
            app       = "optimizer-api"
            component = "backend"
          }
        )
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = tostring(var.metrics_port)
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.optimizer.metadata[0].name

        container {
          name  = "api"
          image = "${var.api_image}:${var.api_image_tag}"

          port {
            name           = "http"
            container_port = 8000
            protocol       = "TCP"
          }

          port {
            name           = "metrics"
            container_port = var.metrics_port
            protocol       = "TCP"
          }

          env {
            name = "POSTGRES_HOST"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres_credentials.metadata[0].name
                key  = "host"
              }
            }
          }

          env {
            name = "POSTGRES_PORT"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres_credentials.metadata[0].name
                key  = "port"
              }
            }
          }

          env {
            name = "POSTGRES_DB"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres_credentials.metadata[0].name
                key  = "database"
              }
            }
          }

          env {
            name = "POSTGRES_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres_credentials.metadata[0].name
                key  = "username"
              }
            }
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres_credentials.metadata[0].name
                key  = "password"
              }
            }
          }

          env {
            name = "REDIS_HOST"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.redis_credentials.metadata[0].name
                key  = "host"
              }
            }
          }

          env {
            name = "REDIS_PORT"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.redis_credentials.metadata[0].name
                key  = "port"
              }
            }
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.optimizer_config.metadata[0].name
            }
          }

          resources {
            limits = {
              cpu    = var.api_resources_limits_cpu
              memory = var.api_resources_limits_memory
            }
            requests = {
              cpu    = var.api_resources_requests_cpu
              memory = var.api_resources_requests_memory
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          image_pull_policy = var.image_pull_policy
        }

        image_pull_secrets {
          name = var.image_pull_secret_name
        }
      }
    }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_surge       = "25%"
        max_unavailable = "25%"
      }
    }
  }
}

# Optimizer API Service
resource "kubernetes_service" "optimizer_api" {
  metadata {
    name      = "optimizer-api"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels = merge(
      var.common_labels,
      {
        app = "optimizer-api"
      }
    )
    annotations = var.service_annotations
  }

  spec {
    type = var.service_type

    selector = {
      app       = "optimizer-api"
      component = "backend"
    }

    port {
      name        = "http"
      port        = 8000
      target_port = 8000
      protocol    = "TCP"
    }

    port {
      name        = "metrics"
      port        = var.metrics_port
      target_port = var.metrics_port
      protocol    = "TCP"
    }
  }
}

# Dashboard Deployment
resource "kubernetes_deployment" "dashboard" {
  metadata {
    name      = "optimizer-dashboard"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels = merge(
      var.common_labels,
      {
        app       = "optimizer-dashboard"
        component = "frontend"
      }
    )
  }

  spec {
    replicas = var.dashboard_replicas

    selector {
      match_labels = {
        app       = "optimizer-dashboard"
        component = "frontend"
      }
    }

    template {
      metadata {
        labels = merge(
          var.common_labels,
          {
            app       = "optimizer-dashboard"
            component = "frontend"
          }
        )
      }

      spec {
        container {
          name  = "dashboard"
          image = "${var.dashboard_image}:${var.dashboard_image_tag}"

          port {
            name           = "http"
            container_port = 80
            protocol       = "TCP"
          }

          resources {
            limits = {
              cpu    = var.dashboard_resources_limits_cpu
              memory = var.dashboard_resources_limits_memory
            }
            requests = {
              cpu    = var.dashboard_resources_requests_cpu
              memory = var.dashboard_resources_requests_memory
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 10
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }

          image_pull_policy = var.image_pull_policy
        }

        image_pull_secrets {
          name = var.image_pull_secret_name
        }
      }
    }
  }
}

# Dashboard Service
resource "kubernetes_service" "dashboard" {
  metadata {
    name      = "optimizer-dashboard"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels = merge(
      var.common_labels,
      {
        app = "optimizer-dashboard"
      }
    )
  }

  spec {
    type = var.service_type

    selector = {
      app       = "optimizer-dashboard"
      component = "frontend"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 80
      protocol    = "TCP"
    }
  }
}

# Ingress (optional)
resource "kubernetes_ingress_v1" "optimizer" {
  count = var.enable_ingress ? 1 : 0

  metadata {
    name      = "optimizer-ingress"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels    = var.common_labels
    annotations = merge(
      var.ingress_annotations,
      {
        "kubernetes.io/ingress.class"                = var.ingress_class
        "cert-manager.io/cluster-issuer"             = var.cert_manager_issuer
        "nginx.ingress.kubernetes.io/ssl-redirect"   = "true"
        "nginx.ingress.kubernetes.io/proxy-body-size" = "50m"
      }
    )
  }

  spec {
    dynamic "tls" {
      for_each = var.enable_tls ? [1] : []
      content {
        hosts       = [var.domain_name]
        secret_name = "${var.namespace}-tls"
      }
    }

    rule {
      host = var.domain_name

      http {
        path {
          path      = "/api"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.optimizer_api.metadata[0].name
              port {
                number = 8000
              }
            }
          }
        }

        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.dashboard.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}

# Horizontal Pod Autoscaler for API
resource "kubernetes_horizontal_pod_autoscaler_v2" "optimizer_api" {
  count = var.enable_hpa ? 1 : 0

  metadata {
    name      = "optimizer-api-hpa"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels    = var.common_labels
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.optimizer_api.metadata[0].name
    }

    min_replicas = var.hpa_min_replicas
    max_replicas = var.hpa_max_replicas

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = var.hpa_target_cpu_utilization
        }
      }
    }

    metric {
      type = "Resource"
      resource {
        name = "memory"
        target {
          type                = "Utilization"
          average_utilization = var.hpa_target_memory_utilization
        }
      }
    }
  }
}

# Network Policy (if enabled)
resource "kubernetes_network_policy" "optimizer" {
  count = var.enable_network_policy ? 1 : 0

  metadata {
    name      = "optimizer-network-policy"
    namespace = kubernetes_namespace.optimizer.metadata[0].name
    labels    = var.common_labels
  }

  spec {
    pod_selector {
      match_labels = {
        app = "optimizer-api"
      }
    }

    policy_types = ["Ingress", "Egress"]

    ingress {
      from {
        pod_selector {
          match_labels = {
            app = "optimizer-dashboard"
          }
        }
      }

      from {
        namespace_selector {
          match_labels = {
            name = "ingress-nginx"
          }
        }
      }

      ports {
        port     = "8000"
        protocol = "TCP"
      }
    }

    egress {
      to {
        namespace_selector {}
      }

      ports {
        port     = "53"
        protocol = "UDP"
      }
    }

    egress {
      to {
        ip_block {
          cidr = "0.0.0.0/0"
          except = [
            "169.254.169.254/32"
          ]
        }
      }
    }
  }
}
