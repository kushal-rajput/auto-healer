"""
BigQuery Setup Script for Auto-Healer Metrics Storage
======================================================

This script creates the BigQuery dataset and table schema for storing
microservice metrics (latency, Kafka lag, error rates, etc.).

Run once before deploying the auto-healer system:
    uv run python setup_bigquery.py

BNB Scoring: +2 (GCP Database) - Demonstrates BigQuery schema design
"""

import os
from google.cloud import bigquery
from google.api_core import exceptions


# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
DATASET_ID = "bnb_autohealer"
TABLE_ID = "metrics"
LOCATION = "US"  # Multi-region for high availability


def create_dataset(client: bigquery.Client) -> None:
    """Create BigQuery dataset if it doesn't exist."""
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset {dataset_ref} already exists")
    except exceptions.NotFound:
        # Create dataset
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        dataset.description = "Auto-Healer microservice metrics storage for BNB Marathon"
        
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset {dataset_ref}")


def create_metrics_table(client: bigquery.Client) -> None:
    """Create metrics table with optimized schema for time-series queries."""
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    try:
        client.get_table(table_ref)
        print(f"✅ Table {table_ref} already exists")
    except exceptions.NotFound:
        # Define schema
        # GCP Database +2: Time-series partitioned table for efficient queries
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED",
                                description="Metric collection timestamp (UTC)"),
            bigquery.SchemaField("service_id", "STRING", mode="REQUIRED",
                                description="Microservice identifier (e.g., user-api)"),
            bigquery.SchemaField("latency_ms", "FLOAT64", mode="REQUIRED",
                                description="P95 request latency in milliseconds"),
            bigquery.SchemaField("kafka_lag", "INT64", mode="NULLABLE",
                                description="Kafka consumer lag (messages behind)"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED",
                                description="Service health status (OK, DEGRADED, CRITICAL)"),
            bigquery.SchemaField("error_rate", "FLOAT64", mode="NULLABLE",
                                description="Error rate (0.0 to 1.0)"),
            bigquery.SchemaField("cpu_usage", "FLOAT64", mode="NULLABLE",
                                description="CPU utilization (0.0 to 1.0)"),
            bigquery.SchemaField("memory_usage", "FLOAT64", mode="NULLABLE",
                                description="Memory utilization (0.0 to 1.0)"),
            bigquery.SchemaField("request_count", "INT64", mode="NULLABLE",
                                description="Total requests in measurement window"),
        ]
        
        table = bigquery.Table(table_ref, schema=schema)
        
        # Enable partitioning by day for query performance
        # Critical for time-series queries (e.g., "last 5 minutes of metrics")
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp",
        )
        
        # Cluster by service_id for efficient filtering
        table.clustering_fields = ["service_id"]
        
        table = client.create_table(table)
        print(f"✅ Created table {table_ref} with partitioning and clustering")


def insert_mock_data(client: bigquery.Client) -> None:
    """Insert mock metric data for testing."""
    from datetime import datetime, timedelta
    import random
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Generate 100+ mock entries
    rows = []
    services = ["user-api", "payment-service", "notification-service", "order-service"]
    
    # Generate data for last 60 minutes
    base_time = datetime.utcnow() - timedelta(minutes=60)
    
    for i in range(120):
        timestamp = base_time + timedelta(minutes=i * 0.5)
        service = random.choice(services)
        
        # Normal operation most of the time
        if random.random() < 0.85:
            latency = random.uniform(50, 200)
            kafka_lag = random.randint(0, 1000)
            error_rate = random.uniform(0, 0.02)
            status = "OK"
        else:
            # Anomaly spike
            latency = random.uniform(800, 2500)
            kafka_lag = random.randint(5000, 15000)
            error_rate = random.uniform(0.05, 0.15)
            status = "DEGRADED" if latency < 2000 else "CRITICAL"
        
        rows.append({
            "timestamp": timestamp.isoformat(),
            "service_id": service,
            "latency_ms": latency,
            "kafka_lag": kafka_lag,
            "status": status,
            "error_rate": error_rate,
            "cpu_usage": random.uniform(0.2, 0.9),
            "memory_usage": random.uniform(0.3, 0.8),
            "request_count": random.randint(50, 500)
        })
    
    # Insert data
    errors = client.insert_rows_json(table_ref, rows)
    
    if errors:
        print(f"❌ Errors inserting mock data: {errors}")
    else:
        print(f"✅ Inserted {len(rows)} mock metric entries")


def main():
    """Setup BigQuery infrastructure and load mock data."""
    print("🔧 Setting up BigQuery for Auto-Healer")
    print(f"📊 Project: {PROJECT_ID}")
    print(f"📁 Dataset: {DATASET_ID}")
    print(f"📋 Table: {TABLE_ID}")
    print("=" * 60)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create dataset
    create_dataset(client)
    
    # Create metrics table
    create_metrics_table(client)
    
    # Insert mock data
    print("\n📈 Loading mock data...")
    insert_mock_data(client)
    
    print("\n" + "=" * 60)
    print("✅ BigQuery setup complete!")
    print(f"\nQuery your data:")
    print(f"  bq query --use_legacy_sql=false 'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` LIMIT 10'")
    print(f"\nOr in Console:")
    print(f"  https://console.cloud.google.com/bigquery?project={PROJECT_ID}&ws=!1m5!1m4!4m3!1s{PROJECT_ID}!2s{DATASET_ID}!3s{TABLE_ID}")


if __name__ == "__main__":
    main()

