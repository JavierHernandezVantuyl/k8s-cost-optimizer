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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workload_id, timestamp)
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

CREATE TABLE IF NOT EXISTS optimization_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workload_id UUID REFERENCES workloads(id) ON DELETE CASCADE,
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE SET NULL,
    change_type VARCHAR(100) NOT NULL,
    old_config JSONB,
    new_config JSONB,
    cost_before DECIMAL(10, 2),
    cost_after DECIMAL(10, 2),
    savings_realized DECIMAL(10, 2),
    applied_by VARCHAR(255),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_metrics_workload_timestamp ON metrics(workload_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cost_estimates_workload_timestamp ON cost_estimates(workload_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_workload_status ON recommendations(workload_id, status);
CREATE INDEX IF NOT EXISTS idx_recommendations_created ON recommendations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workloads_cluster ON workloads(cluster_id);
CREATE INDEX IF NOT EXISTS idx_workloads_namespace ON workloads(namespace);
CREATE INDEX IF NOT EXISTS idx_optimization_history_workload ON optimization_history(workload_id);
CREATE INDEX IF NOT EXISTS idx_optimization_history_applied ON optimization_history(applied_at DESC);

INSERT INTO clusters (name, provider, region, node_count) VALUES
    ('aws-cluster', 'aws', 'us-east-1', 3),
    ('gcp-cluster', 'gcp', 'us-central1', 2),
    ('azure-cluster', 'azure', 'eastus', 2)
ON CONFLICT (name) DO NOTHING;
