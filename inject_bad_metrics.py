#!/usr/bin/env python3
"""
Inject bad metrics into BigQuery for demo purposes.
This creates metrics that exceed thresholds to trigger healing.
"""

from google.cloud import bigquery
from datetime import datetime, timezone, timedelta
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "bnb-marathon-478505")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "bnb_autohealer")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "metrics")

def inject_bad_metrics():
    """Insert metrics that will trigger anomaly detection"""
    
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Current time
    now = datetime.now(timezone.utc)
    
    # Create 5 bad metric samples over last 5 minutes
    bad_metrics = []
    for i in range(5):
        timestamp = now - timedelta(minutes=4-i)  # 4, 3, 2, 1, 0 minutes ago
        
        metric = {
            "timestamp": timestamp.isoformat(),
            "service_id": "user-api",
            "latency_ms": 1800 + (i * 100),  # 1800-2200ms (exceeds 1500ms threshold)
            "kafka_lag": 8000 + (i * 500),   # 8000-10000 (exceeds 5000 threshold)
            "status": "DEGRADED",
            "error_rate": 0.08 + (i * 0.01), # 8-12% (exceeds 5% threshold)
            "cpu_usage": 0.75 + (i * 0.02),  # 75-83%
            "memory_usage": 0.70 + (i * 0.02), # 70-78%
            "request_count": 1500 + (i * 100)
        }
        bad_metrics.append(metric)
    
    # Insert into BigQuery
    print(f"🔧 Injecting {len(bad_metrics)} bad metrics into BigQuery...")
    print(f"   Table: {table_ref}")
    print()
    
    errors = client.insert_rows_json(table_ref, bad_metrics)
    
    if errors:
        print("❌ Errors occurred:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("✅ Bad metrics injected successfully!")
        print()
        print("📊 Metrics summary:")
        for i, metric in enumerate(bad_metrics, 1):
            print(f"   Sample {i}: latency={metric['latency_ms']}ms, "
                  f"kafka_lag={metric['kafka_lag']}, "
                  f"error_rate={metric['error_rate']:.1%}")
        print()
        print("🎯 Thresholds:")
        print("   • Latency: >1500ms (CRITICAL)")
        print("   • Kafka lag: >5000 (WARNING)")
        print("   • Error rate: >5% (CRITICAL)")
        print()
        print("✅ These metrics will trigger anomaly detection!")
        print()
        print("Next step: Run the Auto-Healer:")
        print('   curl -X POST $ROOT_URL/heal \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"service": "user-api", "alert_message": "Demo"}\' | jq .')
        return True

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("   INJECTING BAD METRICS FOR DEMO")
    print("=" * 70)
    print()
    
    try:
        success = inject_bad_metrics()
        if success:
            print()
            print("=" * 70)
            print("   READY FOR DEMO!")
            print("=" * 70)
            print()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

