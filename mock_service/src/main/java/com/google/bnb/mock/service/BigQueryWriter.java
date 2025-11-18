package com.google.bnb.mock.service;

import com.google.cloud.bigquery.*;
import com.google.bnb.mock.model.HealthResponse;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * BigQuery Writer Service
 * 
 * Writes health metrics to BigQuery in real-time for the Auto-Healer system.
 * 
 * This demonstrates the continuous metrics flow from microservice → BigQuery
 * that enables real-time anomaly detection and AI-powered healing.
 * 
 * In production, this pattern is used by:
 * - Netflix (1 trillion events/day to BigQuery)
 * - Spotify (streaming metrics for recommendation systems)
 * - Airbnb (real-time pricing analytics)
 * 
 * Alternative Approaches:
 * - Cloud Logging sink to BigQuery (zero-code solution)
 * - Pub/Sub → Dataflow → BigQuery (for high-throughput)
 * - REST API batching (for cost optimization)
 * 
 * @author Kunal Rajput
 */
@Service
public class BigQueryWriter {
    
    private final BigQuery bigQuery;
    private final String projectId;
    private final String datasetId;
    private final String tableId;
    private final boolean enabled;
    
    public BigQueryWriter() {
        // Initialize BigQuery client
        // Uses Application Default Credentials from environment
        this.projectId = System.getenv().getOrDefault("GCP_PROJECT_ID", "your-project-id");
        this.datasetId = "bnb_autohealer";
        this.tableId = "metrics";
        this.enabled = !projectId.equals("your-project-id");
        
        if (enabled) {
            this.bigQuery = BigQueryOptions.newBuilder()
                .setProjectId(projectId)
                .build()
                .getService();
            System.out.println("✅ BigQuery Writer initialized for project: " + projectId);
        } else {
            this.bigQuery = null;
            System.out.println("⚠️  BigQuery Writer disabled (GCP_PROJECT_ID not set)");
        }
    }
    
    /**
     * Write health metrics to BigQuery.
     * 
     * This method is called on every /health endpoint request, creating a
     * continuous stream of metrics for real-time analysis.
     * 
     * @param response Health response with metrics
     * @return true if write succeeded, false otherwise
     */
    public boolean writeMetric(HealthResponse response) {
        if (!enabled) {
            // Skip if BigQuery not configured (local dev mode)
            return false;
        }
        
        try {
            // Construct row matching BigQuery schema
            Map<String, Object> row = new HashMap<>();
            row.put("timestamp", response.getTimestamp());
            row.put("service_id", response.getService());
            row.put("latency_ms", response.getLatencyMs());
            row.put("kafka_lag", response.getKafkaLag());
            row.put("status", response.getStatus());  // "OK", "DEGRADED", "CRITICAL"
            row.put("error_rate", response.getErrorRate());
            
            // Calculate CPU/memory based on latency (simulation)
            double cpuUsage = Math.min(0.9, response.getLatencyMs() / 2000.0);
            double memoryUsage = Math.min(0.85, response.getKafkaLag() / 20000.0 + 0.3);
            
            row.put("cpu_usage", cpuUsage);
            row.put("memory_usage", memoryUsage);
            row.put("request_count", 1);  // Increment per request
            
            // Get table reference
            TableId tableRef = TableId.of(projectId, datasetId, tableId);
            
            // Insert row (streaming insert for low latency)
            InsertAllRequest insertRequest = InsertAllRequest.newBuilder(tableRef)
                .addRow(row)
                .build();
            
            InsertAllResponse insertResponse = bigQuery.insertAll(insertRequest);
            
            if (insertResponse.hasErrors()) {
                System.err.println("❌ BigQuery insert errors: " + insertResponse.getInsertErrors());
                return false;
            }
            
            return true;
            
        } catch (BigQueryException e) {
            System.err.println("❌ BigQuery error: " + e.getMessage());
            return false;
        } catch (Exception e) {
            System.err.println("❌ Unexpected error writing to BigQuery: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * Check if BigQuery writer is enabled and ready.
     */
    public boolean isEnabled() {
        return enabled;
    }
}

