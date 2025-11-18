# AI-Driven Microservices Auto-Healer

An intelligent auto-healing system for microservices using Google Cloud Platform's AI and serverless technologies.

## 🚀 Overview

This system automatically detects, predicts, and heals microservice failures using:
- **BigQuery**: Time-series metrics storage and analysis
- **Vertex AI/Gemini**: AI-powered risk prediction and decision making
- **Cloud Run**: Serverless deployment and auto-scaling
- **FastMCP**: Secure, callable tools for healing actions
- **ADK (Agent Development Kit)**: Multi-agent orchestration

## 🏗️ Architecture

```
Microservices → BigQuery → Auto-Healer Agents → Healing Actions
                              ↓
                         Gemini AI
```

### Components:
1. **Root Agent**: Orchestrates the healing workflow
2. **Detector Agent**: Analyzes metrics from BigQuery
3. **Predictor Agent**: Uses Gemini AI for risk assessment
4. **Healer Agent**: Executes healing actions (scaling, restart)
5. **MCP Tools**: FastMCP server providing healing capabilities

## 📋 Prerequisites

- Google Cloud Project with billing enabled
- Python 3.12+
- Java 17+ (for mock service)
- `gcloud` CLI configured
- `uv` Python package manager

## 🛠️ Setup

### 1. Clone and Setup Environment

```bash
# Install dependencies
uv sync

# Set up environment variables
cp env.example .env
# Edit .env with your GCP project details
```

### 2. Initialize BigQuery

```bash
uv run python setup_bigquery.py
```

### 3. Deploy to Cloud Run

```bash
chmod +x deploy.sh
./deploy.sh
```

## 🎯 Usage

### Trigger Auto-Healing

```bash
curl -X POST https://your-root-agent-url/heal \
  -H "Content-Type: application/json" \
  -d '{"service": "user-api"}'
```

### Inject Test Metrics

```bash
uv run python inject_bad_metrics.py
```

## 📊 Monitoring

- **Cloud Run Console**: Monitor service health and logs
- **BigQuery Console**: View metrics data
- **Cloud Scheduler**: Automated healing triggers

## 🏆 BNB Marathon Submission

This project demonstrates:
- ✅ Cloud Run for serverless deployment
- ✅ BigQuery for time-series data
- ✅ Vertex AI/Gemini for intelligent predictions
- ✅ Multi-agent orchestration with ADK
- ✅ Production-ready auto-healing system

## 📝 License

MIT License

## 👥 Authors

Built for Google BNB Marathon 2025

