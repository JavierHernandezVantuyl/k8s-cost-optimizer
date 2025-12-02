# EKS Module Outputs

output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_oidc_provider_arn" {
  description = "OIDC provider ARN"
  value       = module.eks.oidc_provider_arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.db.db_instance_endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.db.db_instance_name
}

output "rds_port" {
  description = "RDS port"
  value       = module.db.db_instance_port
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.optimizer_data.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.optimizer_data.arn
}

output "cost_optimizer_role_arn" {
  description = "IAM role ARN for cost optimizer"
  value       = aws_iam_role.cost_optimizer.arn
}

output "cluster_autoscaler_role_arn" {
  description = "IAM role ARN for cluster autoscaler"
  value       = aws_iam_role.cluster_autoscaler.arn
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${data.aws_availability_zones.available.id} --name ${module.eks.cluster_name}"
}
