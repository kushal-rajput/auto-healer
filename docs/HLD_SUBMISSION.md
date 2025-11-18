# Auto-Healer – High Level Design (BNB Marathon 2025)

---

## 1. Executive Snapshot
- **Problem**: Microservice incidents still rely on 2–4 hour manual runbooks, static scaling, and post-impact firefighting.  
- **Solution**: A serverless, multi-agent auto-healer that *Detects → Predicts → Heals → Verifies* in <10 seconds using BigQuery telemetry and Vertex AI Gemini.  
- **Impact**:

| Metric | Before | After |
|--------|--------|-------|
| Mean Time To Recovery | 2–4 hours | **< 10 seconds** |
| Human intervention | On-call SRE | **Zero** (fully autonomous) |
| Scaling accuracy | Static 2–10 instances | **Adaptive 3–15+** based on risk |

---

## 2. Architecture Overview
- Refer to `high_level_design_diagram.mmd` (rendered view: `arch_dia.png`).  
- Design principles: serverless-first, AI-in-the-loop, event-driven, opinionated MTTR guardrails, and full observability.

**Lanes**
1. **Entry Points** – SRE alert, Cloud Scheduler, or Pub/Sub POST `/heal`.  
2. **Root Agent (Cloud Run, Python 3.12 + ADK)** – Orchestrates Detector, Predictor, Healer agents.  
3. **MCP Tools Server (FastAPI + FastMCP)** – Toolchain (`get_metrics`, `detect_anomaly`, `predict_risk`, `scale_service`, `restart_service`, `verify_health`, `ingest_metrics`).  
4. **Target Microservices (Cloud Run, Java 17)** – `user-api` exports `/health` metrics and receives scaling actions.  
5. **Data Plane** – BigQuery partitioned table + Cloud Logging traces.  
6. **AI Reasoning** – Vertex AI Gemini 1.5 Pro returns risk score and action recommendation.  
7. **Closure & Feedback** – JSON runbook output + dashboards for demo storytelling.

---

## 3. Component Responsibilities
| Lane | Responsibilities | Notes |
|------|------------------|-------|
| Entry Points | Cron, alert, or manual trigger to `/heal`. | Same interface for demo + production. |
| Root Agent | Routes workflow, enforces SLAs, aggregates result JSON. | Stateless Cloud Run revision (FastAPI + ADK). |
| Detector Agent | Calls `get_metrics` + `detect_anomaly`; thresholds: latency>1500 ms, kafka lag>5000, error rate>5%, CPU>80%, memory>85%. | BigQuery query time <100 ms. |
| Predictor Agent | Sends metrics + violations to Gemini (`temperature=0.2`) for deterministic recommendations. | Response ~1.5 s, JSON structured. |
| Healer Agent | Executes `scale_service` or `restart_service`, waits 3 s, then `verify_health`. | gcloud CLI wrapped inside MCP tool. |
| Data Plane | BigQuery streaming inserts from Java service; Cloud Logging centralizes traces. | Dataset `bnb_autohealer.metrics`, partitioned daily, clustered by `service_id`. |
| Feedback | Emits full evidence package: metrics snapshot, risk, action, verification, execution time (<10 s). | Drives console + blog storyline. |

---

## 4. Healing Flow & Timings (Detect → Predict → Heal → Verify)
1. **Trigger (0 s)**: `/heal` invoked with service name + optional alert context.  
2. **Detect (≤5 s)**: Detector queries BigQuery (last 5 min) and runs rule-based anomaly detection.  
3. **Predict (≤2 s)**: Predictor sends context to Gemini; receives `risk_score (0-100)` and `recommended_action`.  
4. **Heal (≤3 s)**: Healer adjusts Cloud Run min/max instances (e.g., 2-10 ➜ 3-15) or restarts service.  
5. **Verify (≤2 s)**: `verify_health` hits `/health`, confirms config drift cleared, and re-reads BigQuery to ensure metrics trending healthy.  
6. **Report (instant)**: Root Agent returns signed JSON plus Cloud Logging trace; dashboards refresh automatically.  
**Total MTTR**: consistently under 10 seconds end-to-end.

---

## 5. Technology Footprint & Deployment
| Stack Element | Implementation |
|---------------|----------------|
| Cloud Run | 3 services (`user-api`, `autohealer-mcp-tools`, `autohealer-root-agent`), europe-west1, auto-scaling 1–100 instances, 80 concurrency. |
| BigQuery | Streaming inserts, partition-by-day + cluster-by-service; <130 demo rows but proven for millions/day. |
| Vertex AI | Gemini 1.5 Pro, JSON mode, temperature 0.2, SDK via `google-cloud-aiplatform`. |
| Languages & Frameworks | Python 3.12 (FastAPI, FastMCP, httpx, Pydantic) + Java 17 (Spring Boot). |
| Deployment | Docker images + `deploy.sh` (gcloud). Service accounts per component with least-privilege IAM. |

---

## 6. Reliability, Security & Observability
- **Reliability**: Multi-agent separation avoids cascading failures; retries + timeout policies per tool; Cloud Run revisions provide instant rollback.  
- **Security**: IAM-scoped service accounts (`BigQuery Data Viewer`, `Vertex AI User`, `Cloud Run Admin`); TLS everywhere; no static keys in code.  
- **Observability**:  
  - Structured logs: `service`, `phase`, `violations`, `risk_score`, `action_taken`.  
  - Metrics: Cloud Run latency/P95, instance counts, healing success rate (custom log-based metric).  
  - Alerts (next iteration): healing failure >10%, MCP latency >5 s, BigQuery cost alarms.

---

## 7. Expansion Plan
- **Phase 2**: Predictive scaling (LSTM), cost-aware sizing recommendations, richer policy library inside ADK.  
- **Phase 3**: Multi-cloud + database auto-healing, PagerDuty/Slack integrations for optional human-in-the-loop controls.  
- **Phase 4**: Self-learning policy loop (reinforcement learning on healing outcomes) and continuous optimization of anomaly thresholds.  

---

