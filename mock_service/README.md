# Mock Microservice for Auto-Healer Demo

## Overview

This is a Java 17 Spring Boot application that simulates a production microservice with controllable failure modes. It's used to test the AI-Driven Auto-Healer by injecting latency spikes and Kafka consumer lag.

## Features

- **Health Check Endpoint**: `/health` with normal/degraded states
- **Failure Injection**: Query parameter `?fail=true` triggers anomalies
- **Metrics Export**: `/metrics` endpoint for Prometheus/BigQuery
- **Cloud Run Ready**: Startup/liveness probes configured

## Build & Run

### Local Development

```bash
# Build
mvn clean package

# Run
java -jar target/mock-microservice-1.0.0.jar

# Or with Maven
mvn spring-boot:run
```

### Test Endpoints

```bash
# Healthy service
curl http://localhost:8080/health
# Response: {"status":"healthy","latency_ms":120,"kafka_lag":450}

# Inject failure
curl http://localhost:8080/health?fail=true
# Response: {"status":"degraded","latency_ms":1850,"kafka_lag":8500}

# Get metrics
curl http://localhost:8080/metrics
```

### Deploy to Cloud Run

```bash
# Set project ID
export GCP_PROJECT_ID=your-project-id

# Build and push container with Jib
mvn compile jib:build

# Deploy to Cloud Run
gcloud run deploy mock-microservice \
  --image gcr.io/$GCP_PROJECT_ID/mock-microservice:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 5 \
  --cpu 1 \
  --memory 512Mi
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         HealthController                    │
│  • GET /health (normal/fail modes)          │
│  • POST /health/inject (chaos engineering)  │
│  • GET /metrics (export)                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        MetricsSimulator                     │
│  • Track latency, Kafka lag, error rate    │
│  • Simulate CPU/memory usage                │
│  • Support failure mode (chaos)             │
└─────────────────────────────────────────────┘
```

## Integration with Auto-Healer

1. **Mock service** runs on Cloud Run (simulates production microservice)
2. **Metrics exporter** (separate script) polls `/metrics` → writes to BigQuery
3. **Auto-Healer** queries BigQuery → detects anomalies → scales mock service
4. **Demo flow**: Healthy → Inject failure → Auto-Healer heals → Recovered

## BNB Marathon Alignment

- **Cloud Run Usage**: Deployed as serverless Java service
- **Industry Impact**: Realistic simulation of production microservice patterns (Spring Boot, Kafka, latency spikes)
- **Functional Demo**: E2E healing workflow with observable before/after states

