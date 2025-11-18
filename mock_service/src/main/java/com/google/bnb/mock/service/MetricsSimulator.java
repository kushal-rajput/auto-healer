package com.google.bnb.mock.service;

import org.springframework.stereotype.Service;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Metrics Simulator Service
 * 
 * This service tracks and simulates microservice metrics for export to BigQuery.
 * In a real system, these metrics would come from actual application behavior.
 * 
 * Purpose:
 * - Store current metric state (for /metrics endpoint)
 * - Support chaos engineering (controlled failure injection)
 * - Generate realistic metric patterns (gradual vs. sudden spikes)
 * 
 * @author Kunal Rajput
 */
@Service
public class MetricsSimulator {
    
    private final AtomicInteger currentLatency = new AtomicInteger(100);
    private final AtomicInteger currentKafkaLag = new AtomicInteger(500);
    private final AtomicInteger requestCount = new AtomicInteger(0);
    private final AtomicBoolean failureMode = new AtomicBoolean(false);
    private final AtomicLong failureModeEndTime = new AtomicLong(0);
    
    /**
     * Record a metric observation.
     * 
     * This would typically be called by application instrumentation
     * (e.g., Micrometer, OpenTelemetry) and exported to BigQuery via Cloud Logging.
     */
    public void recordMetric(int latency, int kafkaLag, double errorRate) {
        currentLatency.set(latency);
        currentKafkaLag.set(kafkaLag);
        requestCount.incrementAndGet();
        
        // Auto-resolve failure mode after timeout
        if (failureMode.get() && System.currentTimeMillis() > failureModeEndTime.get()) {
            failureMode.set(false);
        }
    }
    
    /**
     * Enable failure mode for chaos engineering.
     */
    public void setFailureMode(boolean enabled, int durationSeconds) {
        this.failureMode.set(enabled);
        if (enabled) {
            this.failureModeEndTime.set(System.currentTimeMillis() + (durationSeconds * 1000L));
        }
    }
    
    /**
     * Get current metrics snapshot.
     */
    public ServiceMetrics getCurrentMetrics() {
        ServiceMetrics metrics = new ServiceMetrics();
        metrics.setLatencyMs(currentLatency.get());
        metrics.setKafkaLag(currentKafkaLag.get());
        metrics.setRequestCount(requestCount.get());
        
        // Simulate CPU/memory usage based on latency
        double cpuUsage = Math.min(0.9, currentLatency.get() / 2000.0);
        double memoryUsage = Math.min(0.85, currentKafkaLag.get() / 20000.0 + 0.3);
        
        metrics.setCpuUsage(cpuUsage);
        metrics.setMemoryUsage(memoryUsage);
        
        // Error rate correlates with latency
        double errorRate = currentLatency.get() > 1000 ? 0.05 : 0.01;
        metrics.setErrorRate(errorRate);
        
        return metrics;
    }
    
    /**
     * Service Metrics POJO.
     */
    public static class ServiceMetrics {
        private int latencyMs;
        private int kafkaLag;
        private double errorRate;
        private double cpuUsage;
        private double memoryUsage;
        private int requestCount;
        
        // Getters and Setters
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
        
        public double getCpuUsage() {
            return cpuUsage;
        }
        
        public void setCpuUsage(double cpuUsage) {
            this.cpuUsage = cpuUsage;
        }
        
        public double getMemoryUsage() {
            return memoryUsage;
        }
        
        public void setMemoryUsage(double memoryUsage) {
            this.memoryUsage = memoryUsage;
        }
        
        public int getRequestCount() {
            return requestCount;
        }
        
        public void setRequestCount(int requestCount) {
            this.requestCount = requestCount;
        }
    }
}

