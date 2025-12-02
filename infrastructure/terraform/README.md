# Terraform Infrastructure

Production-ready Terraform modules for deploying K8s Cost Optimizer infrastructure on AWS, GCP, or Azure.

## Modules

### Cloud Provider Modules

- **eks/**: AWS EKS cluster with VPC, RDS, ElastiCache, S3
- **gke/**: GCP GKE cluster with VPC, Cloud SQL, Memorystore, GCS
- **aks/**: Azure AKS cluster with VNet, PostgreSQL, Redis Cache, Blob Storage
- **optimizer/**: Kubernetes resources for optimizer deployment

## Quick Start

### 1. Configure Backend

Edit `environments/<env>/main.tf` to configure your Terraform backend:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "k8s-cost-optimizer/dev/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### 2. Set Variables

Copy the example variables file:

```bash
cp environments/dev/terraform.tfvars.example environments/dev/terraform.tfvars
```

Edit `terraform.tfvars` with your values.

### 3. Deploy

```bash
cd environments/dev
terraform init
terraform plan
terraform apply
```

## Module Usage

### EKS Module

```hcl
module "eks" {
  source = "../../modules/eks"

  cluster_name             = "optimizer-dev"
  kubernetes_version       = "1.28"
  environment              = "dev"
  cost_center              = "development"

  # VPC Configuration
  vpc_cidr                 = "10.0.0.0/16"
  private_subnet_cidrs     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnet_cidrs      = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  # Node Configuration
  system_node_instance_types = ["t3.medium"]
  system_node_min_size       = 2
  system_node_max_size       = 4
  system_node_desired_size   = 2

  app_node_instance_types    = ["t3.large"]
  app_node_min_size          = 2
  app_node_max_size          = 10
  app_node_desired_size      = 3

  # Database Configuration
  db_instance_class          = "db.t3.medium"
  db_allocated_storage       = 20
  db_max_allocated_storage   = 100

  # Redis Configuration
  redis_node_type            = "cache.t3.micro"

  # S3 Configuration
  cost_optimizer_bucket      = "optimizer-dev-data"

  common_tags = {
    Project     = "k8s-cost-optimizer"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}
```

### GKE Module

```hcl
module "gke" {
  source = "../../modules/gke"

  project_id               = "your-project-id"
  cluster_name             = "optimizer-dev"
  region                   = "us-central1"
  environment              = "dev"
  cost_center              = "development"

  # Network Configuration
  subnet_cidr              = "10.0.0.0/24"
  pods_cidr                = "10.1.0.0/16"
  services_cidr            = "10.2.0.0/16"

  # Node Configuration
  system_node_machine_type = "e2-medium"
  system_node_min_count    = 2
  system_node_max_count    = 4

  app_node_machine_type    = "e2-standard-2"
  app_node_min_count       = 2
  app_node_max_count       = 10
  app_node_preemptible     = false

  # Database Configuration
  db_tier                  = "db-f1-micro"
  db_disk_size             = 20

  # Redis Configuration
  redis_memory_size_gb     = 1

  # Storage Configuration
  optimizer_bucket_name    = "optimizer-dev-data"

  common_labels = {
    project     = "k8s-cost-optimizer"
    environment = "dev"
    managed_by  = "terraform"
  }
}
```

### AKS Module

```hcl
module "aks" {
  source = "../../modules/aks"

  cluster_name             = "optimizer-dev"
  location                 = "eastus"
  environment              = "dev"
  cost_center              = "development"

  # Network Configuration
  vnet_address_space       = "10.0.0.0/16"
  aks_subnet_cidr          = "10.0.1.0/24"
  postgres_subnet_cidr     = "10.0.2.0/24"

  # Node Configuration
  system_node_vm_size      = "Standard_D2s_v3"
  system_node_min_count    = 2
  system_node_max_count    = 4

  app_node_vm_size         = "Standard_D4s_v3"
  app_node_min_count       = 2
  app_node_max_count       = 10
  app_node_spot_enabled    = false

  # Database Configuration
  db_sku_name              = "B_Standard_B1ms"
  db_storage_mb            = 32768

  # Redis Configuration
  redis_sku_name           = "Standard"
  redis_family             = "C"
  redis_capacity           = 0

  common_tags = {
    Project     = "k8s-cost-optimizer"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}
```

### Optimizer Module

```hcl
module "optimizer" {
  source = "../../modules/optimizer"

  namespace                = "cost-optimizer"
  environment              = "dev"
  cost_center              = "development"

  # Database (from EKS/GKE/AKS module outputs)
  postgres_host            = module.eks.rds_endpoint
  postgres_port            = 5432
  postgres_database        = "k8s_optimizer"
  postgres_username        = "optimizer"
  postgres_password        = var.db_password

  # Redis (from EKS/GKE/AKS module outputs)
  redis_host               = module.eks.redis_endpoint
  redis_port               = 6379
  redis_password           = ""

  # Storage (from EKS/GKE/AKS module outputs)
  storage_endpoint         = "s3.amazonaws.com"
  storage_access_key       = var.storage_access_key
  storage_secret_key       = var.storage_secret_key
  storage_bucket           = module.eks.s3_bucket_name

  # Application Configuration
  log_level                = "DEBUG"
  metrics_enabled          = true
  analysis_interval        = "1h"
  min_confidence_threshold = 0.6
  enable_auto_apply        = false
  dry_run_mode             = true

  # Deployment Configuration
  api_image                = "your-registry/optimizer-api"
  api_image_tag            = "dev"
  api_replicas             = 1

  dashboard_image          = "your-registry/optimizer-dashboard"
  dashboard_image_tag      = "dev"
  dashboard_replicas       = 1

  # Service Configuration
  enable_ingress           = true
  domain_name              = "optimizer-dev.example.com"

  # IAM Configuration (AWS only)
  aws_iam_role_arn         = module.eks.cost_optimizer_role_arn

  common_labels = {
    project     = "k8s-cost-optimizer"
    environment = "dev"
  }
}
```

## Outputs

Each module provides outputs for resource references:

```bash
# View outputs
terraform output

# Example outputs
configure_kubectl = "aws eks update-kubeconfig --name optimizer-dev"
cluster_endpoint  = "https://XXXXX.eks.amazonaws.com"
api_endpoint      = "optimizer-api.cost-optimizer.svc.cluster.local:8000"
```

## State Management

### Remote State

Configure remote state backend in `main.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "cost-optimizer/dev"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State Locking

Use DynamoDB for state locking (AWS):

```bash
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```

## Cost Optimization

### Estimated Monthly Costs

**Development**:
- EKS: ~$75 (cluster) + ~$30 (nodes) = ~$105
- RDS: ~$15 (db.t3.micro)
- ElastiCache: ~$12 (cache.t3.micro)
- **Total**: ~$132/month

**Production**:
- EKS: ~$75 (cluster) + ~$150 (nodes) = ~$225
- RDS: ~$60 (db.t3.medium, multi-AZ)
- ElastiCache: ~$50 (cache.t3.medium, multi-AZ)
- **Total**: ~$335/month

### Cost Tags

All resources are tagged with:
- `Environment`
- `CostCenter`
- `ManagedBy`
- `Project`

View costs:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --filter file://filter.json \
  --metrics UnblendedCost
```

## Security

### Sensitive Variables

Never commit secrets to Git. Use:

1. **Environment Variables**:
   ```bash
   export TF_VAR_db_password="secret"
   ```

2. **Variable Files** (gitignored):
   ```bash
   echo "terraform.tfvars" >> .gitignore
   ```

3. **Secret Managers**:
   ```hcl
   data "aws_secretsmanager_secret_version" "db_password" {
     secret_id = "optimizer/db-password"
   }
   ```

### IAM Roles

EKS uses IRSA (IAM Roles for Service Accounts):

```hcl
aws_iam_role_arn = module.eks.cost_optimizer_role_arn
```

## Troubleshooting

### Common Issues

1. **"Error creating VPC"**
   - Check AWS quotas: `aws service-quotas get-service-quota --service-code vpc --quota-code L-F678F1CE`

2. **"Error creating RDS"**
   - Verify subnet groups span at least 2 AZs

3. **"Provider configuration not found"**
   ```bash
   terraform init -upgrade
   ```

4. **"State lock acquisition failed"**
   ```bash
   terraform force-unlock <lock-id>
   ```

## Best Practices

1. **Use modules**: Don't duplicate code
2. **Version constraints**: Pin provider versions
3. **State backends**: Always use remote state
4. **Separate environments**: Use workspaces or directories
5. **Tag everything**: Enable cost tracking
6. **Plan before apply**: Always review changes
7. **Automate with CI/CD**: Use GitHub Actions

## Maintenance

### Upgrading Kubernetes

```bash
# Update variable
kubernetes_version = "1.29"

# Plan and apply
terraform plan
terraform apply
```

### Scaling Nodes

```bash
# Update variables
app_node_desired_size = 5

terraform apply
```

### Destroying Resources

```bash
# Destroy specific environment
cd environments/dev
terraform destroy

# Destroy specific resource
terraform destroy -target=module.eks
```

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [AKS Best Practices](https://learn.microsoft.com/en-us/azure/aks/best-practices)
