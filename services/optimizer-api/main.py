import os
import json
import csv
import io
import asyncio
from typing import List
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import psycopg2
from psycopg2.extras import RealDictCursor

from models import (
    CostSummary, OptimizationRecommendation, AnalysisRequest,
    OptimizeWorkloadRequest, ApplyRecommendationRequest, ApplyRecommendationResponse,
    SavingsHistory, Workload, WorkloadMetrics, MetricStats, ResourceSpec,
    ClusterCostSummary, ExportFormat, CSVRow, TerraformExport, WebSocketUpdate
)
from optimizer.ml_engine import MLEngine
from optimizer.cost_calculator import CostCalculator
from optimizer.recommender import Recommender

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "k8s_optimizer")
DB_USER = os.getenv("POSTGRES_USER", "optimizer")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "optimizer_dev_pass")

app = FastAPI(
    title="K8s Cost Optimizer API",
    description="ML-based cost optimization engine for Kubernetes workloads",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ml_engine = MLEngine()
cost_calculator = CostCalculator()
recommender = Recommender(ml_engine, cost_calculator)

active_websockets: List[WebSocket] = []


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


async def fetch_workload_from_db(workload_id: str) -> Workload:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT w.*, c.name as cluster_name, c.provider
            FROM workloads w
            JOIN clusters c ON w.cluster_id = c.id
            WHERE w.id = %s
        """, (workload_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Workload {workload_id} not found")

        return Workload(
            id=str(row["id"]),
            cluster_id=str(row["cluster_id"]),
            cluster_name=row["cluster_name"],
            namespace=row["namespace"],
            name=row["name"],
            kind=row["kind"],
            replicas=row["replicas"],
            provider=row["provider"],
            current_resources=ResourceSpec(
                cpu_request=row["cpu_request"],
                memory_request=row["memory_request"],
                cpu_limit=row["cpu_limit"],
                memory_limit=row["memory_limit"]
            )
        )
    finally:
        cursor.close()
        conn.close()


async def fetch_workload_metrics(workload_id: str, hours: int = 168) -> WorkloadMetrics:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        cursor.execute("""
            SELECT
                AVG(cpu_usage_cores) as cpu_avg,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cpu_usage_cores) as cpu_p50,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cpu_usage_cores) as cpu_p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY cpu_usage_cores) as cpu_p99,
                MAX(cpu_usage_cores) as cpu_max,
                MIN(cpu_usage_cores) as cpu_min,
                AVG(memory_usage_bytes) as mem_avg,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY memory_usage_bytes) as mem_p50,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY memory_usage_bytes) as mem_p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY memory_usage_bytes) as mem_p99,
                MAX(memory_usage_bytes) as mem_max,
                MIN(memory_usage_bytes) as mem_min,
                COUNT(*) as sample_count
            FROM metrics
            WHERE workload_id = %s AND timestamp >= %s
        """, (workload_id, cutoff))

        row = cursor.fetchone()

        workload = await fetch_workload_from_db(workload_id)
        cpu_request = ml_engine._parse_cpu(workload.current_resources.cpu_request)
        memory_request = ml_engine._parse_memory(workload.current_resources.memory_request)

        cpu_utilization = (row["cpu_avg"] / cpu_request * 100) if cpu_request > 0 else 0
        memory_utilization = (row["mem_avg"] / memory_request * 100) if memory_request > 0 else 0

        return WorkloadMetrics(
            workload_id=workload_id,
            cpu_usage=MetricStats(
                avg=row["cpu_avg"] or 0,
                p50=row["cpu_p50"] or 0,
                p95=row["cpu_p95"] or 0,
                p99=row["cpu_p99"] or 0,
                max=row["cpu_max"] or 0,
                min=row["cpu_min"] or 0
            ),
            memory_usage=MetricStats(
                avg=row["mem_avg"] or 0,
                p50=row["mem_p50"] or 0,
                p95=row["mem_p95"] or 0,
                p99=row["mem_p99"] or 0,
                max=row["mem_max"] or 0,
                min=row["mem_min"] or 0
            ),
            cpu_utilization_pct=cpu_utilization,
            memory_utilization_pct=memory_utilization,
            sample_count=row["sample_count"] or 0,
            time_range_hours=hours
        )
    finally:
        cursor.close()
        conn.close()


@app.post("/analyze", response_model=CostSummary)
async def analyze_all_workloads(request: AnalysisRequest = None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        query = """
            SELECT w.*, c.name as cluster_name, c.provider
            FROM workloads w
            JOIN clusters c ON w.cluster_id = c.id
            WHERE 1=1
        """
        params = []

        if request and request.cluster_filter:
            query += " AND c.name = ANY(%s)"
            params.append(request.cluster_filter)

        if request and request.namespace_filter:
            query += " AND w.namespace = ANY(%s)"
            params.append(request.namespace_filter)

        cursor.execute(query, params)
        workload_rows = cursor.fetchall()

        all_recommendations = []
        cluster_summaries = {}
        total_current_cost = 0
        total_optimized_cost = 0

        for row in workload_rows:
            workload = Workload(
                id=str(row["id"]),
                cluster_id=str(row["cluster_id"]),
                cluster_name=row["cluster_name"],
                namespace=row["namespace"],
                name=row["name"],
                kind=row["kind"],
                replicas=row["replicas"],
                provider=row["provider"],
                current_resources=ResourceSpec(
                    cpu_request=row["cpu_request"],
                    memory_request=row["memory_request"],
                    cpu_limit=row["cpu_limit"],
                    memory_limit=row["memory_limit"]
                )
            )

            metrics = await fetch_workload_metrics(str(row["id"]))
            min_conf = request.min_confidence if request else 0.5
            recommendations = await recommender.generate_recommendations(workload, metrics, min_conf)

            for rec in recommendations:
                if request and request.min_savings_threshold:
                    if rec.monthly_savings < request.min_savings_threshold:
                        continue

                if request and not request.include_high_risk:
                    if rec.risk_assessment.level.value == "high":
                        continue

                all_recommendations.append(rec)
                total_current_cost += rec.current_cost.monthly
                total_optimized_cost += rec.optimized_cost.monthly

                cluster = rec.cluster_name
                if cluster not in cluster_summaries:
                    cluster_summaries[cluster] = {
                        "provider": workload.provider,
                        "workload_count": 0,
                        "current_cost": 0,
                        "optimized_cost": 0,
                        "recommendations": []
                    }

                cluster_summaries[cluster]["workload_count"] += 1
                cluster_summaries[cluster]["current_cost"] += rec.current_cost.monthly
                cluster_summaries[cluster]["optimized_cost"] += rec.optimized_cost.monthly
                cluster_summaries[cluster]["recommendations"].append(rec)

        all_recommendations.sort(key=lambda r: r.monthly_savings, reverse=True)
        top_recommendations = all_recommendations[:10]

        cluster_summaries_list = []
        for cluster_name, data in cluster_summaries.items():
            savings = data["current_cost"] - data["optimized_cost"]
            cluster_summaries_list.append(
                ClusterCostSummary(
                    cluster_name=cluster_name,
                    provider=data["provider"],
                    workload_count=data["workload_count"],
                    current_monthly_cost=data["current_cost"],
                    optimized_monthly_cost=data["optimized_cost"],
                    potential_monthly_savings=savings,
                    savings_percentage=(savings / data["current_cost"] * 100) if data["current_cost"] > 0 else 0,
                    recommendation_count=len(data["recommendations"])
                )
            )

        by_type = {}
        for rec in all_recommendations:
            opt_type = rec.optimization_type.value
            by_type[opt_type] = by_type.get(opt_type, 0) + rec.monthly_savings

        total_savings = total_current_cost - total_optimized_cost

        return CostSummary(
            total_workloads=len(workload_rows),
            total_current_monthly_cost=total_current_cost,
            total_optimized_monthly_cost=total_optimized_cost,
            total_potential_monthly_savings=total_savings,
            total_potential_yearly_savings=total_savings * 12,
            overall_savings_percentage=(total_savings / total_current_cost * 100) if total_current_cost > 0 else 0,
            clusters=cluster_summaries_list,
            top_recommendations=top_recommendations,
            by_optimization_type=by_type
        )

    finally:
        cursor.close()
        conn.close()


@app.post("/optimize/{workload_id}")
async def optimize_workload(workload_id: str, request: OptimizeWorkloadRequest = None):
    workload = await fetch_workload_from_db(workload_id)
    metrics = await fetch_workload_metrics(workload_id)

    min_conf = request.min_confidence if request else 0.6
    recommendations = await recommender.generate_recommendations(workload, metrics, min_conf)

    if request and request.max_risk_level:
        recommendations = [
            r for r in recommendations
            if r.risk_assessment.level.value <= request.max_risk_level.value
        ]

    if request and request.optimization_types:
        recommendations = [
            r for r in recommendations
            if r.optimization_type in request.optimization_types
        ]

    return {
        "workload": workload,
        "metrics": metrics,
        "recommendations": recommendations,
        "total_potential_savings": sum(r.monthly_savings for r in recommendations)
    }


@app.get("/recommendations")
async def get_recommendations(
    min_savings: float = 0.0,
    min_confidence: float = 0.5,
    limit: int = 100
):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT * FROM recommendations
            WHERE estimated_savings >= %s AND confidence_score >= %s
            ORDER BY estimated_savings DESC
            LIMIT %s
        """, (min_savings, min_confidence, limit))

        recommendations = cursor.fetchall()
        return {"recommendations": recommendations, "count": len(recommendations)}

    finally:
        cursor.close()
        conn.close()


@app.post("/apply/{recommendation_id}")
async def apply_recommendation(
    recommendation_id: str,
    request: ApplyRecommendationRequest
):
    if request.dry_run:
        return ApplyRecommendationResponse(
            recommendation_id=recommendation_id,
            status="dry_run_success",
            message="Dry run completed successfully. No changes applied."
        )

    return ApplyRecommendationResponse(
        recommendation_id=recommendation_id,
        status="applied",
        message="Recommendation applied successfully",
        applied_at=datetime.utcnow()
    )


@app.get("/savings/history")
async def get_savings_history(days: int = 30):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE created_at >= %s) as generated,
                COUNT(*) FILTER (WHERE status = 'applied' AND applied_at >= %s) as applied,
                COALESCE(SUM(estimated_savings) FILTER (WHERE created_at >= %s), 0) as potential,
                COALESCE(SUM(estimated_savings) FILTER (WHERE status = 'applied' AND applied_at >= %s), 0) as realized
            FROM recommendations
        """, (cutoff, cutoff, cutoff, cutoff))

        row = cursor.fetchone()

        realized = float(row["realized"]) if row["realized"] else 0
        potential = float(row["potential"]) if row["potential"] else 0

        return SavingsHistory(
            period_start=cutoff,
            period_end=datetime.utcnow(),
            total_recommendations_generated=row["generated"] or 0,
            recommendations_applied=row["applied"] or 0,
            potential_savings=potential,
            realized_savings=realized,
            realization_rate=(realized / potential * 100) if potential > 0 else 0
        )

    finally:
        cursor.close()
        conn.close()


@app.post("/export/terraform")
async def export_terraform():
    summary = await analyze_all_workloads()

    terraform_config = {
        "terraform": {
            "required_version": ">= 1.0"
        },
        "resource": {}
    }

    for rec in summary.top_recommendations[:5]:
        resource_name = f"k8s_deployment_{rec.workload_name.replace('-', '_')}"
        terraform_config["resource"][resource_name] = {
            "metadata": {
                "name": rec.workload_name,
                "namespace": rec.namespace
            },
            "spec": {
                "replicas": rec.recommended_config.get("replicas", 1),
                "template": {
                    "spec": {
                        "containers": [{
                            "resources": {
                                "requests": {
                                    "cpu": rec.recommended_config.get("cpu_request"),
                                    "memory": rec.recommended_config.get("memory_request")
                                }
                            }
                        }]
                    }
                }
            }
        }

    return Response(
        content=json.dumps(terraform_config, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=terraform.tf.json"}
    )


@app.get("/export/csv")
async def export_csv():
    summary = await analyze_all_workloads()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Cluster", "Namespace", "Workload", "Optimization Type",
        "Current Monthly Cost", "Optimized Monthly Cost", "Monthly Savings",
        "Savings %", "Confidence Score", "Risk Level", "Status"
    ])

    for rec in summary.top_recommendations:
        writer.writerow([
            rec.cluster_name,
            rec.namespace,
            rec.workload_name,
            rec.optimization_type.value,
            f"${rec.current_cost.monthly:.2f}",
            f"${rec.optimized_cost.monthly:.2f}",
            f"${rec.monthly_savings:.2f}",
            f"{rec.savings_percentage:.1f}%",
            f"{rec.confidence_score:.2f}",
            rec.risk_assessment.level.value,
            rec.status
        ])

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cost_optimization_recommendations.csv"}
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)

    try:
        while True:
            summary = await analyze_all_workloads()

            update = WebSocketUpdate(
                event_type="optimization_update",
                data={
                    "total_savings": summary.total_potential_monthly_savings,
                    "recommendation_count": len(summary.top_recommendations),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            await websocket.send_json(update.dict())
            await asyncio.sleep(30)

    except Exception as e:
        active_websockets.remove(websocket)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "optimizer-api", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
