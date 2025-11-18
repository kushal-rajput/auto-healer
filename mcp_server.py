"""
Simple HTTP wrapper for MCP tools
This provides HTTP endpoints for all MCP tools for easier testing and deployment
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import os
import subprocess

# BigQuery setup
from google.cloud import bigquery

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "bnb-marathon-478505")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "bnb_autohealer")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "metrics")
BIGQUERY_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Initialize BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID)

app = FastAPI(
    title="Auto-Healer MCP Tools API",
    description="HTTP wrapper for MCP tools",
    version="1.0.0"
)

# Request models
class DetectAnomalyRequest(BaseModel):
    service_name: str
    time_window_minutes: int = 5
    latency_threshold_ms: float = 500.0
    kafka_lag_threshold: int = 5000

class GetMetricsRequest(BaseModel):
    service_name: str
    limit: int = 10

class PredictRiskRequest(BaseModel):
    service_name: str
    metrics: Dict[str, Any]

class IngestMetricsRequest(BaseModel):
    service_url: str
    service_name: str = "user-api"

class ScaleServiceRequest(BaseModel):
    service_name: str
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_utilization: int = 70

class RestartServiceRequest(BaseModel):
    service_name: str

class VerifyHealthRequest(BaseModel):
    service_name: str


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "autohealer-mcp-tools",
        "tools": 7
    }


@app.post("/tools/detect_anomaly")
async def detect_anomaly(request: DetectAnomalyRequest):
    """Detect anomalies in service metrics"""
    try:
        # Calculate time window for query
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=request.time_window_minutes)
        
        # BigQuery SQL: Aggregate metrics over time window
        query = f"""
        SELECT
            service_id,
            AVG(latency_ms) as avg_latency_ms,
            MAX(latency_ms) as max_latency_ms,
            AVG(kafka_lag) as avg_kafka_lag,
            MAX(kafka_lag) as max_kafka_lag,
            COUNT(*) as sample_count,
            AVG(error_rate) as avg_error_rate,
            COUNT(CASE WHEN status = 'DEGRADED' THEN 1 END) as degraded_count,
            COUNT(CASE WHEN status = 'CRITICAL' THEN 1 END) as critical_count
        FROM
            `{BIGQUERY_TABLE}`
        WHERE
            service_id = @service_name
            AND timestamp >= @start_time
            AND timestamp <= @end_time
        GROUP BY
            service_id
        """
        
        # Configure query with parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("service_name", "STRING", request.service_name),
                bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
                bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
            ]
        )
        
        # Execute query
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            return {
                "anomaly_detected": False,
                "service": request.service_name,
                "metrics": None,
                "violations": [],
                "query_time": end_time.isoformat(),
                "recommendation": f"No metrics found for {request.service_name} in last {request.time_window_minutes} minutes. Verify service is running and exporting metrics.",
                "error": "NO_DATA"
            }
        
        row = results[0]
        
        # Extract metrics
        metrics = {
            "avg_latency_ms": float(row.avg_latency_ms or 0),
            "max_latency_ms": float(row.max_latency_ms or 0),
            "avg_kafka_lag": float(row.avg_kafka_lag or 0),
            "max_kafka_lag": float(row.max_kafka_lag or 0),
            "avg_error_rate": float(row.avg_error_rate or 0),
            "sample_count": int(row.sample_count)
        }
        
        # Detect violations
        violations = []
        anomaly_detected = False
        
        if metrics["avg_latency_ms"] > request.latency_threshold_ms:
            violations.append(
                f"Latency violation: {metrics['avg_latency_ms']:.2f}ms exceeds threshold {request.latency_threshold_ms}ms"
            )
            anomaly_detected = True
        
        if metrics["avg_kafka_lag"] > request.kafka_lag_threshold:
            violations.append(
                f"Kafka lag violation: {metrics['avg_kafka_lag']:.0f} messages exceeds threshold {request.kafka_lag_threshold}"
            )
            anomaly_detected = True
        
        if metrics["avg_error_rate"] > 0.05:
            violations.append(
                f"Error rate violation: {metrics['avg_error_rate']*100:.2f}% exceeds 5% threshold"
            )
            anomaly_detected = True
        
        # Generate recommendation
        if anomaly_detected:
            recommendation = (
                f"CRITICAL: {request.service_name} requires immediate attention. "
                f"Recommend scaling replicas and investigating root cause. "
                f"Violations: {len(violations)}"
            )
        else:
            recommendation = f"{request.service_name} operating within normal parameters."
        
        return {
            "anomaly_detected": anomaly_detected,
            "service": request.service_name,
            "metrics": metrics,
            "violations": violations,
            "time_window_minutes": request.time_window_minutes,
            "query_time": end_time.isoformat(),
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/get_metrics")
async def get_metrics(request: GetMetricsRequest):
    """Get recent metrics for a service"""
    try:
        query = f"""
        SELECT
            timestamp,
            service_id,
            latency_ms,
            kafka_lag,
            status,
            error_rate,
            cpu_usage,
            memory_usage,
            request_count
        FROM
            `{BIGQUERY_TABLE}`
        WHERE
            service_id = @service_name
        ORDER BY
            timestamp DESC
        LIMIT
            @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("service_name", "STRING", request.service_name),
                bigquery.ScalarQueryParameter("limit", "INT64", request.limit),
            ]
        )
        
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        metrics = []
        for row in results:
            metrics.append({
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "service_id": row.service_id,
                "latency_ms": float(row.latency_ms or 0),
                "kafka_lag": int(row.kafka_lag or 0),
                "status": row.status,
                "error_rate": float(row.error_rate or 0),
                "cpu_usage": float(row.cpu_usage or 0),
                "memory_usage": float(row.memory_usage or 0),
                "request_count": int(row.request_count or 0)
            })
        
        return {
            "success": True,
            "service": request.service_name,
            "count": len(metrics),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/predict_risk")
async def predict_risk(request: PredictRiskRequest):
    """Predict failure risk using Gemini AI"""
    try:
        from google.cloud import aiplatform
        from vertexai.generative_models import GenerativeModel
        import vertexai
        import json
        
        project_id = os.getenv("GCP_PROJECT_ID", PROJECT_ID)
        location = os.getenv("VERTEX_AI_LOCATION", "europe-west1")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        vertexai.init(project=project_id, location=location)
        gemini = GenerativeModel(model_name)
        
        prompt = f"""Analyze these microservice metrics and respond with ONLY valid JSON.

Service: {request.service_name}
Metrics: {json.dumps(request.metrics)}

IMPORTANT: recommended_action MUST be one of: scale_up, restart, monitor, escalate_human

Respond with this EXACT JSON format (no markdown, no extra text):
{{"risk_score": 85, "root_cause": "High latency indicates resource constraints", "recommended_action": "scale_up", "confidence": "high", "reasoning": "Service requires scaling"}}

Analyze and return ONLY the JSON:"""
        
        response = gemini.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Lower temperature for more consistent output
                "top_p": 0.8,
                "top_k": 20,
                "max_output_tokens": 2048,  # Increased from 1024
            }
        )
        response_text = response.text.strip()
        
        # Debug: Log FULL raw response on first attempt
        print(f"🤖 GEMINI RAW RESPONSE (len={len(response_text)}): {repr(response_text)}")
        
        # Validate response is complete (has matching braces)
        if response_text.count("{") != response_text.count("}"):
            print(f"⚠️ TRUNCATED RESPONSE detected! Braces: {{ {response_text.count('{')} }} {response_text.count('}')}")
            # Use fallback prediction based on metrics
            avg_latency = request.metrics.get("avg_latency_ms", 0)
            error_rate = request.metrics.get("avg_error_rate", 0)
            if avg_latency > 1500 or error_rate > 0.05:
                prediction = {
                    "risk_score": 85,
                    "root_cause": "High latency and error rate indicate resource constraints",
                    "recommended_action": "scale_up",
                    "confidence": "high",
                    "reasoning": "Metrics exceed thresholds, scaling recommended"
                }
            else:
                prediction = {
                    "risk_score": 50,
                    "root_cause": "Minor performance degradation detected",
                    "recommended_action": "monitor",
                    "confidence": "medium",
                    "reasoning": "Metrics slightly elevated, continue monitoring"
                }
            print(f"✅ Using FALLBACK prediction: {prediction}")
        else:
            # Clean up markdown formatting
            if "```" in response_text:
                # Extract content between code blocks
                parts = response_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part and (part.startswith("{") or part.startswith("[")):
                        response_text = part
                        break
            
            # Find JSON object in response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                response_text = response_text[start:end]
            
            prediction = json.loads(response_text)
            print(f"✅ Successfully parsed Gemini response")
        
        return {
            "success": True,
            "service": request.service_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **prediction
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "service": request.service_name,
            "risk_score": 0,
            "recommended_action": "monitor",
            "confidence": "low",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.post("/tools/ingest_metrics")
async def ingest_metrics(request: IngestMetricsRequest):
    """Ingest metrics from Java service"""
    try:
        import httpx
        response = httpx.get(f"{request.service_url}/metrics", timeout=10.0)
        response.raise_for_status()
        metrics_data = response.json()
        
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_id": request.service_name,
            "latency_ms": float(metrics_data.get("latency_ms", 0)),
            "kafka_lag": int(metrics_data.get("kafka_lag", 0)),
            "status": "DEGRADED" if metrics_data.get("latency_ms", 0) > 500 else "OK",
            "error_rate": float(metrics_data.get("error_rate", 0)),
            "cpu_usage": float(metrics_data.get("cpu_usage", 0)),
            "memory_usage": float(metrics_data.get("memory_usage", 0)),
            "request_count": int(metrics_data.get("request_count", 0))
        }
        
        errors = bq_client.insert_rows_json(BIGQUERY_TABLE, [row])
        if errors:
            return {
                "success": False,
                "service": request.service_name,
                "errors": errors,
                "message": f"Failed to insert metrics: {errors}"
            }
        
        return {
            "success": True,
            "service": request.service_name,
            "rows_inserted": 1,
            "timestamp": row["timestamp"],
            "message": f"Successfully ingested metrics for {request.service_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/scale_service")
async def scale_service(request: ScaleServiceRequest):
    """Scale a Cloud Run service"""
    try:
        project_id = os.getenv("GCP_PROJECT_ID", PROJECT_ID)
        region = os.getenv("CLOUD_RUN_REGION", "europe-west1")
        
        cmd = [
            "gcloud", "run", "services", "update", request.service_name,
            "--region", region,
            "--project", project_id,
            "--min-instances", str(request.min_instances),
            "--max-instances", str(request.max_instances),
            "--cpu-throttling",
            "--format", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return {
                "success": True,
                "service": request.service_name,
                "action": "scaled",
                "min_instances": request.min_instances,
                "max_instances": request.max_instances,
                "region": region,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "success": False,
                "service": request.service_name,
                "error": result.stderr,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/restart_service")
async def restart_service(request: RestartServiceRequest):
    """Restart a Cloud Run service"""
    try:
        project_id = os.getenv("GCP_PROJECT_ID", PROJECT_ID)
        region = os.getenv("CLOUD_RUN_REGION", "europe-west1")
        
        cmd = [
            "gcloud", "run", "services", "update", request.service_name,
            "--region", region,
            "--project", project_id,
            "--update-env-vars", f"RESTART_TIME={datetime.now(timezone.utc).isoformat()}",
            "--format", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return {
                "success": True,
                "service": request.service_name,
                "action": "restarted",
                "region": region,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "success": False,
                "service": request.service_name,
                "error": result.stderr,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/verify_health")
async def verify_health_endpoint(request: VerifyHealthRequest):
    """Verify health of a Cloud Run service"""
    try:
        project_id = os.getenv("GCP_PROJECT_ID", PROJECT_ID)
        region = os.getenv("CLOUD_RUN_REGION", "europe-west1")
        
        cmd = [
            "gcloud", "run", "services", "describe", request.service_name,
            "--region", region,
            "--project", project_id,
            "--format", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            service_info = json.loads(result.stdout)
            status = service_info.get("status", {})
            conditions = status.get("conditions", [])
            
            ready = any(
                c.get("type") == "Ready" and c.get("status") == "True"
                for c in conditions
            )
            
            return {
                "success": True,
                "service": request.service_name,
                "ready": ready,
                "url": service_info.get("status", {}).get("url"),
                "region": region,
                "conditions": conditions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "success": False,
                "service": request.service_name,
                "error": result.stderr,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_SERVER_PORT", os.getenv("PORT", "8081")))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    
    print("🚀 Starting Auto-Healer MCP Tools HTTP Server...")
    print(f"🔌 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")
