# AI-Driven Auto-Healer — Idea Overview

## 1. Elevator Pitch
Production microservices still depend on human runbooks whenever latency spikes, Kafka lag creeps up, or pods crash. The AI-Driven Auto-Healer replaces that manual loop with a serverless, multi-agent system that can **detect**, **predict**, **heal**, and **verify** within ten seconds—using only Google Cloud primitives and Vertex AI Gemini reasoning.

## 2. Problem Landscape
- MTTR for typical microservice incidents remains 2–4 hours even with solid observability.
- On-call rotations suffer from alert fatigue because every regression requires manual inspection.
- Static scaling (fixed min/max instances) either wastes budget or cannot absorb traffic bursts.
- Incidents in upstream services ripple to downstream dependencies, magnifying impact on users.

## 3. Solution Overview
The Auto-Healer combines observability data, prescriptive AI, and automated remediation:
- **Cloud Run + ADK Root Agent**: A FastAPI service where ADK coordinates Detector, Predictor, and Healer agents.
- **MCP Tools Server**: Secure toolbox (get metrics, detect anomaly, predict risk, scale service, restart service, verify health, ingest metrics) exposed as APIs.
- **BigQuery Metrics Lake**: Streaming time-series table that stores latency, kafka lag, error rate, CPU, memory, and request count.
- **Vertex AI Gemini 1.5 Pro**: Interprets anomalies, scores risk (0–100), recommends actions, and explains reasoning in JSON.
- **Java Mock Service**: Cloud Run workload that mimics production behavior and emits `/health` data for demos or tests.

## 4. Core Capabilities
| Stage | What Happens | Outcome |
|-------|--------------|---------|
| **Detect** | Detector agent queries last 5 minutes of BigQuery metrics and checks thresholds (latency>1500 ms, kafka lag>5000, error rate>5%, CPU>80%, memory>85%). | Flags violations instantly. |
| **Predict** | Predictor agent feeds metrics + violations to Gemini (temperature 0.2). | Receives risk score and recommended action (scale_up, restart, none). |
| **Heal** | Healer agent calls MCP tools to adjust Cloud Run min/max instances or restart the service, then waits 3 seconds. | Executes remediation in place. |
| **Verify** | `verify_health` re-checks `/health` and BigQuery to ensure metrics fall back to healthy envelopes. | Confirms success and logs evidence. |

Total MTTR stays **< 10 seconds** because each phase is asynchronous and serverless.

## 5. Google Cloud Footprint
| Service | Role |
|---------|------|
| Cloud Run | Hosts user-api, MCP Tools, and Root Agent (ADK). |
| BigQuery | Low-latency analytics for anomaly detection + reporting. |
| Vertex AI Gemini | Risk evaluation and prescriptive reasoning. |
| Cloud Scheduler / Pub/Sub | Optional triggers for `/heal`. |
| Cloud Logging | Centralized audit of every action and verification. |

## 6. Customer & Business Value
- **SRE Productivity**: Reduces manual toil by ~80%, freeing engineers for proactive work.
- **Reliability**: Cuts user-facing downtime from hours to seconds; prevents cascading failures.
- **Cost Efficiency**: Uses serverless billing models and only scales when risk warrants it.
- **AIOps Showcase**: Demonstrates a production-ready pattern for Google Cloud + Gemini integration.

## 7. Differentiators
1. **ADK Multi-Agent Brain** – Root Agent chooses specialized flows per incident type instead of a single monolithic script.
2. **Explainable Gemini Decisions** – Every action comes with AI reasoning and risk scores stored alongside metrics.
3. **Closed-Loop Verification** – System never assumes success; it validates configuration and health endpoints automatically.
4. **Toolbox Isolation** – MCP tools isolate sensitive operations (gcloud, BigQuery, Vertex AI) behind minimal IAM scopes.

## 8. Sample Demo Narrative
1. SRE triggers `/heal` after noticing elevated latency.  
2. Detector spots latency 2.1 s and Kafka lag 9,200 in BigQuery.  
3. Predictor receives `risk_score: 82`, `recommended_action: "scale_up"`.  
4. Healer bumps Cloud Run min/max from 2–10 to 3–15 instances.  
5. Verify confirms `/health` is green and logs a JSON runbook entry with timings and metrics.

## 9. Expansion Path
- **Phase 2**: Predictive scaling with LSTM models and cost-aware policies.
- **Phase 3**: Multi-cloud service healing, PagerDuty/Slack notifications, and database optimizations.
- **Phase 4**: Self-learning policies where ADK agents adapt thresholds and recommended actions from historic outcomes.

---

For reference metrics used in demos and ML testing, see `docs/03_sample_metrics.md`.
