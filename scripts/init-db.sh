#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS clusters (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(255) NOT NULL UNIQUE,
        provider VARCHAR(50) NOT NULL,
        region VARCHAR(100),
        node_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS workloads (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        cluster_id UUID REFERENCES clusters(id) ON DELETE CASCADE,
        namespace VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        kind VARCHAR(50) NOT NULL,
        replicas INTEGER DEFAULT 1,
        cpu_request VARCHAR(50),
        memory_request VARCHAR(50),
        cpu_limit VARCHAR(50),
        memory_limit VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(cluster_id, namespace, name, kind)
    );

    CREATE TABLE IF NOT EXISTS metrics (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        workload_id UUID REFERENCES workloads(id) ON DELETE CASCADE,
        timestamp TIMESTAMP NOT NULL,
        cpu_usage_cores DECIMAL(10, 4),
        memory_usage_bytes BIGINT,
        network_rx_bytes BIGINT,
        network_tx_bytes BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cost_estimates (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        workload_id UUID REFERENCES workloads(id) ON DELETE CASCADE,
        timestamp TIMESTAMP NOT NULL,
        hourly_cost DECIMAL(10, 4),
        daily_cost DECIMAL(10, 2),
        monthly_cost DECIMAL(10, 2),
        cost_breakdown JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS recommendations (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        workload_id UUID REFERENCES workloads(id) ON DELETE CASCADE,
        recommendation_type VARCHAR(100) NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        current_config JSONB,
        recommended_config JSONB,
        estimated_savings DECIMAL(10, 2),
        confidence_score DECIMAL(3, 2),
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        applied_at TIMESTAMP
    );

    CREATE INDEX idx_metrics_workload_timestamp ON metrics(workload_id, timestamp DESC);
    CREATE INDEX idx_cost_estimates_workload_timestamp ON cost_estimates(workload_id, timestamp DESC);
    CREATE INDEX idx_recommendations_workload_status ON recommendations(workload_id, status);
    CREATE INDEX idx_workloads_cluster ON workloads(cluster_id);

    INSERT INTO clusters (name, provider, region, node_count) VALUES
        ('aws-cluster', 'aws', 'us-east-1', 3),
        ('gcp-cluster', 'gcp', 'us-central1', 2),
        ('azure-cluster', 'azure', 'eastus', 2)
    ON CONFLICT (name) DO NOTHING;

EOSQL

echo "Database initialized successfully"
