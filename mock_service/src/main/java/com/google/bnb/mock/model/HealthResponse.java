package com.google.bnb.mock.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Health Check Response Model
 * 
 * This POJO represents the health status of the microservice,
 * including key performance indicators (KPIs) for SRE monitoring.
 * 
 * Fields mirror the BigQuery schema in setup_bigquery.py for consistency.
 * 
 * @author Kunal Rajput
 */
public class HealthResponse {
    
    private String status;           // "healthy" | "degraded" | "critical"
    private String service;          // Service identifier (e.g., "user-api")
    private String timestamp;        // ISO 8601 timestamp
    
    @JsonProperty("latency_ms")
    private int latencyMs;           // P95 request latency in milliseconds
    
    @JsonProperty("kafka_lag")
    private int kafkaLag;            // Kafka consumer lag (messages behind)
    
    @JsonProperty("error_rate")
    private double errorRate;        // Error rate (0.0 to 1.0)
    
    private String message;          // Human-readable status message
    
    // Constructors
    public HealthResponse() {}
    
    public HealthResponse(String status, String service, int latencyMs, int kafkaLag, double errorRate) {
        this.status = status;
        this.service = service;
        this.latencyMs = latencyMs;
        this.kafkaLag = kafkaLag;
        this.errorRate = errorRate;
    }
    
    // Getters and Setters
    public String getStatus() {
        return status;
    }
    
    public void setStatus(String status) {
        this.status = status;
    }
    
    public String getService() {
        return service;
    }
    
    public void setService(String service) {
        this.service = service;
    }
    
    public String getTimestamp() {
        return timestamp;
    }
    
    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
    
    public int getLatencyMs() {
        return latencyMs;
    }
    
    public void setLatencyMs(int latencyMs) {
        this.latencyMs = latencyMs;
    }
    
    public int getKafkaLag() {
        return kafkaLag;
    }
    
    public void setKafkaLag(int kafkaLag) {
        this.kafkaLag = kafkaLag;
    }
    
    public double getErrorRate() {
        return errorRate;
    }
    
    public void setErrorRate(double errorRate) {
        this.errorRate = errorRate;
    }
    
    public String getMessage() {
        return message;
    }
    
    public void setMessage(String message) {
        this.message = message;
    }
}

