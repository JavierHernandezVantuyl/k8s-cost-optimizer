import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import psycopg2
from psycopg2.extras import execute_batch
from prometheus_client import start_http_server, Gauge, Counter
import schedule

from workload_generator import WorkloadGenerator
from metrics_simulator import MetricsSimulator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "k8s_optimizer")
DB_USER = os.getenv("POSTGRES_USER", "optimizer")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "optimizer_dev_pass")

METRICS_PORT = int(os.getenv("METRICS_PORT", "8001"))
GENERATION_INTERVAL = int(os.getenv("GENERATION_INTERVAL", "60"))

cpu_usage_gauge = Gauge(
    'k8s_workload_cpu_usage_cores',
    'CPU usage in cores',
    ['cluster', 'namespace', 'workload', 'kind']
)

memory_usage_gauge = Gauge(
    'k8s_workload_memory_usage_bytes',
    'Memory usage in bytes',
    ['cluster', 'namespace', 'workload', 'kind']
)

network_rx_gauge = Gauge(
    'k8s_workload_network_rx_bytes',
    'Network receive bytes',
    ['cluster', 'namespace', 'workload', 'kind']
)

network_tx_gauge = Gauge(
    'k8s_workload_network_tx_bytes',
    'Network transmit bytes',
    ['cluster', 'namespace', 'workload', 'kind']
)

metrics_generated_counter = Counter(
    'metrics_generator_total',
    'Total metrics generated',
    ['cluster']
)


class MetricsGenerator:

    def __init__(self):
        self.workload_gen = WorkloadGenerator()
        self.metrics_sim = MetricsSimulator()
        self.db_conn = None
        self.workload_ids = {}

    def connect_db(self):
        max_retries = 10
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to database (attempt {attempt + 1}/{max_retries})...")
                self.db_conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    dbname=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
                self.db_conn.autocommit = False
                logger.info("Database connection established")
                return
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise

    def initialize_workloads(self):
        logger.info("Initializing workloads in database...")

        clusters = ["aws-cluster", "gcp-cluster", "azure-cluster"]
        cursor = self.db_conn.cursor()

        try:
            for cluster in clusters:
                cursor.execute(
                    "SELECT id FROM clusters WHERE name = %s",
                    (cluster,)
                )
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"Cluster {cluster} not found in database")
                    continue

                cluster_id = result[0]
                workloads = self.workload_gen.get_workloads_by_cluster(cluster)

                logger.info(f"Initializing {len(workloads)} workloads for {cluster}...")

                for workload in workloads:
                    cursor.execute(
                        """
                        INSERT INTO workloads (
                            cluster_id, namespace, name, kind, replicas,
                            cpu_request, memory_request, cpu_limit, memory_limit
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (cluster_id, namespace, name, kind)
                        DO UPDATE SET
                            replicas = EXCLUDED.replicas,
                            cpu_request = EXCLUDED.cpu_request,
                            memory_request = EXCLUDED.memory_request,
                            cpu_limit = EXCLUDED.cpu_limit,
                            memory_limit = EXCLUDED.memory_limit,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                        """,
                        (
                            cluster_id,
                            workload["namespace"],
                            workload["name"],
                            workload["kind"],
                            workload["replicas"],
                            workload["cpu_request"],
                            workload["memory_request"],
                            workload["cpu_limit"],
                            workload["memory_limit"]
                        )
                    )

                    workload_id = cursor.fetchone()[0]
                    key = f"{cluster}:{workload['namespace']}:{workload['name']}"
                    self.workload_ids[key] = (workload_id, workload)

            self.db_conn.commit()
            logger.info(f"Initialized {len(self.workload_ids)} workloads")

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to initialize workloads: {e}")
            raise
        finally:
            cursor.close()

    def generate_historical_data(self, days: int = 7):
        logger.info(f"Generating {days} days of historical data...")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        cursor = self.db_conn.cursor()

        try:
            batch_data = []
            batch_size = 1000

            for key, (workload_id, workload) in self.workload_ids.items():
                logger.info(f"Generating historical metrics for {key}...")

                historical_metrics = self.metrics_sim.generate_historical_metrics(
                    workload,
                    start_time,
                    end_time,
                    interval_minutes=30
                )

                for metric in historical_metrics:
                    batch_data.append((
                        workload_id,
                        metric["timestamp"],
                        metric["cpu_usage_cores"],
                        metric["memory_usage_bytes"],
                        metric["network_rx_bytes"],
                        metric["network_tx_bytes"]
                    ))

                    if len(batch_data) >= batch_size:
                        execute_batch(
                            cursor,
                            """
                            INSERT INTO metrics (
                                workload_id, timestamp, cpu_usage_cores,
                                memory_usage_bytes, network_rx_bytes, network_tx_bytes
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (workload_id, timestamp) DO NOTHING
                            """,
                            batch_data
                        )
                        self.db_conn.commit()
                        logger.info(f"Inserted batch of {len(batch_data)} metrics")
                        batch_data = []

            if batch_data:
                execute_batch(
                    cursor,
                    """
                    INSERT INTO metrics (
                        workload_id, timestamp, cpu_usage_cores,
                        memory_usage_bytes, network_rx_bytes, network_tx_bytes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (workload_id, timestamp) DO NOTHING
                    """,
                    batch_data
                )
                self.db_conn.commit()
                logger.info(f"Inserted final batch of {len(batch_data)} metrics")

            logger.info("Historical data generation complete")

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to generate historical data: {e}")
            raise
        finally:
            cursor.close()

    def generate_current_metrics(self):
        timestamp = datetime.utcnow()
        cursor = self.db_conn.cursor()

        try:
            batch_data = []

            for key, (workload_id, workload) in self.workload_ids.items():
                cluster, namespace, workload_name = key.split(":")

                cpu_usage = self.metrics_sim.generate_cpu_usage(workload, timestamp)
                memory_usage = self.metrics_sim.generate_memory_usage(workload, timestamp)
                rx_bytes, tx_bytes = self.metrics_sim.generate_network_traffic(workload, timestamp)

                cpu_usage_gauge.labels(
                    cluster=cluster,
                    namespace=namespace,
                    workload=workload_name,
                    kind=workload["kind"]
                ).set(cpu_usage)

                memory_usage_gauge.labels(
                    cluster=cluster,
                    namespace=namespace,
                    workload=workload_name,
                    kind=workload["kind"]
                ).set(memory_usage)

                network_rx_gauge.labels(
                    cluster=cluster,
                    namespace=namespace,
                    workload=workload_name,
                    kind=workload["kind"]
                ).set(rx_bytes)

                network_tx_gauge.labels(
                    cluster=cluster,
                    namespace=namespace,
                    workload=workload_name,
                    kind=workload["kind"]
                ).set(tx_bytes)

                batch_data.append((
                    workload_id,
                    timestamp,
                    cpu_usage,
                    memory_usage,
                    rx_bytes,
                    tx_bytes
                ))

                metrics_generated_counter.labels(cluster=cluster).inc()

            execute_batch(
                cursor,
                """
                INSERT INTO metrics (
                    workload_id, timestamp, cpu_usage_cores,
                    memory_usage_bytes, network_rx_bytes, network_tx_bytes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (workload_id, timestamp) DO NOTHING
                """,
                batch_data
            )
            self.db_conn.commit()

            logger.info(f"Generated metrics for {len(batch_data)} workloads")

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to generate current metrics: {e}")
        finally:
            cursor.close()

    def run(self):
        logger.info("Starting Metrics Generator...")

        self.connect_db()
        self.initialize_workloads()

        generate_historical = os.getenv("GENERATE_HISTORICAL", "true").lower() == "true"
        if generate_historical:
            historical_days = int(os.getenv("HISTORICAL_DAYS", "7"))
            self.generate_historical_data(days=historical_days)

        logger.info(f"Starting Prometheus metrics server on port {METRICS_PORT}...")
        start_http_server(METRICS_PORT)

        schedule.every(GENERATION_INTERVAL).seconds.do(self.generate_current_metrics)

        self.generate_current_metrics()

        logger.info(f"Metrics generation running (interval: {GENERATION_INTERVAL}s)")
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    generator = MetricsGenerator()
    generator.run()
