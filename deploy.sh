#!/bin/bash
# Auto-Healer Deployment Script for Cloud Run
# BNB Marathon - Deploy all components

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${CLOUD_RUN_REGION:-"europe-west1"}  # GPU support for ML models
SERVICE_ACCOUNT="autohealer-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Deploying Auto-Healer to Cloud Run"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "================================================"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# ============================================
# STEP 1: Deploy Java Mock Service
# ============================================
echo ""
echo "📦 Step 1/4: Deploying Java Mock Service..."

cd mock_service
gcloud run deploy user-api \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --service-account $SERVICE_ACCOUNT \
    --min-instances 1 \
    --max-instances 20 \
    --cpu 1 \
    --memory 512Mi \
    --timeout 60 \
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET=bnb_autohealer,BIGQUERY_TABLE=metrics,SPRING_PROFILES_ACTIVE=cloud"

MOCK_URL=$(gcloud run services describe user-api --region $REGION --format="value(status.url)")
echo "✅ Mock Service deployed: $MOCK_URL"

cd ..

# ============================================
# STEP 2: Deploy MCP Tools Server
# ============================================
echo ""
echo "📦 Step 2/4: Deploying MCP Tools Server..."

gcloud run deploy autohealer-mcp-tools \
    --source=. \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 10 \
    --cpu 2 \
    --memory 4Gi \
    --timeout 300 \
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,CLOUD_RUN_REGION=$REGION,BIGQUERY_DATASET=bnb_autohealer,BIGQUERY_TABLE=metrics"

MCP_URL=$(gcloud run services describe autohealer-mcp-tools --region $REGION --format="value(status.url)")
echo "✅ MCP Tools deployed: $MCP_URL"

# ============================================
# STEP 3: Deploy Root Agent
# ============================================
echo ""
echo "📦 Step 3/4: Deploying Root Agent..."

gcloud run deploy autohealer-root-agent \
    --source . \
    --dockerfile Dockerfile.agent \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --service-account $SERVICE_ACCOUNT \
    --min-instances 1 \
    --max-instances 5 \
    --cpu 2 \
    --memory 4Gi \
    --timeout 600 \
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,CLOUD_RUN_REGION=$REGION,MCP_ENDPOINT=$MCP_URL,VERTEX_AI_LOCATION=$REGION,GEMINI_MODEL=gemini-1.5-pro"

ROOT_URL=$(gcloud run services describe autohealer-root-agent --region $REGION --format="value(status.url)")
echo "✅ Root Agent deployed: $ROOT_URL"

# ============================================
# STEP 4: Test Deployment
# ============================================
echo ""
echo "📦 Step 4/4: Testing deployment..."

# Test Mock Service health
echo ""
echo "1️⃣ Testing Mock Service health..."
curl -s "$MOCK_URL/health" | jq .

# Test MCP Tools health
echo ""
echo "2️⃣ Testing MCP Tools health..."
curl -s "$MCP_URL/health" | jq .

# Test Root Agent health
echo ""
echo "3️⃣ Testing Root Agent health..."
curl -s "$ROOT_URL/health" | jq .

# Test metric ingestion
echo ""
echo "4️⃣ Testing metric ingestion from Mock Service..."
curl -s -X POST "$MCP_URL/tools/ingest_metrics" \
  -H "Content-Type: application/json" \
  -d "{\"service_url\": \"$MOCK_URL\", \"service_name\": \"user-api\"}" | jq .

# ============================================
# SUMMARY
# ============================================
echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "🔗 Service URLs:"
echo "   Mock Service:  $MOCK_URL"
echo "   MCP Tools:     $MCP_URL"
echo "   Root Agent:    $ROOT_URL"
echo ""
echo "📋 Demo Commands:"
echo ""
echo "   1. Check Mock Service Health:"
echo "      curl $MOCK_URL/health | jq ."
echo ""
echo "   2. Detect Anomalies:"
echo "      curl -X POST $MCP_URL/tools/detect_anomaly \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"service_name\": \"user-api\", \"time_window_minutes\": 5}' | jq ."
echo ""
echo "   3. Scale the Mock Service:"
echo "      curl -X POST $MCP_URL/tools/scale_service \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"service_name\": \"user-api\", \"min_instances\": 2, \"max_instances\": 10}' | jq ."
echo ""
echo "   4. Restart the Mock Service:"
echo "      curl -X POST $MCP_URL/tools/restart_service \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"service_name\": \"user-api\"}' | jq ."
echo ""
echo "   5. Verify Service Health:"
echo "      curl -X POST $MCP_URL/tools/verify_health \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"service_name\": \"user-api\"}' | jq ."
echo ""
echo "   6. Test Full Healing Workflow:"
echo "      curl -X POST $ROOT_URL/heal \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"service\": \"user-api\", \"alert_message\": \"High latency detected\"}' | jq ."
echo ""
echo "📊 View Logs:"
echo "   Mock Service:  gcloud run logs read user-api --region $REGION"
echo "   MCP Tools:     gcloud run logs read autohealer-mcp-tools --region $REGION"
echo "   Root Agent:    gcloud run logs read autohealer-root-agent --region $REGION"
echo ""
echo "📈 Monitor in Console:"
echo "   https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "================================================"

