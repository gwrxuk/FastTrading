# Production Environment Configuration

environment = "production"
aws_region  = "us-east-1"

# VPC
vpc_cidr             = "10.0.0.0/16"
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# EKS
cluster_name       = "fasttrading-production"
kubernetes_version = "1.28"

# Database - High performance for trading workloads
db_instance_class = "db.r6g.2xlarge"

# Redis - For high-throughput caching
redis_node_type = "cache.r6g.xlarge"

# Kafka - For high-volume event streaming
kafka_instance_type = "kafka.m5.2xlarge"

