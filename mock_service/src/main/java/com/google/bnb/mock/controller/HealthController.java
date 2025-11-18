package com.google.bnb.mock.controller;

import com.google.bnb.mock.model.HealthResponse;
import com.google.bnb.mock.service.MetricsSimulator;
import com.google.bnb.mock.service.BigQueryWriter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Health Check Controller with Failure Injection
 * 
 * This controller provides endpoints for:
 * 1. Normal health checks (for Cloud Run)
 * 2. Simulated failures (latency spikes, Kafka lag)
 * 3. Metrics export (for BigQuery ingestion)
 * 
 * Usage:
 *   GET  /health           - Normal health check
 *   GET  /health?fail=true - Inject latency spike + Kafka lag
 *   POST /health/inject    - Manually trigger failure mode
 *   GET  /metrics          - Export current metrics (Prometheus format)
 * 
 * Industry Context:
 * In production microservices, health endpoints are critical for:
 * - Load balancer routing (Cloud Run/Kubernetes)
 * - Monitoring/alerting (Prometheus scraping)
 * - Chaos engineering (controlled failure injection)
 * 
 * @author Kunal Rajput
 */
@RestController
@RequestMapping
public class HealthController {

    @Autowired
    private MetricsSimulator metricsSimulator;
    
    @Autowired
    private BigQueryWriter bigQueryWriter;

    /**
     * Main health check endpoint.
     * 
     * Query Parameters:
     *   - fail (boolean): If true, simulates degraded state
     *   - latency (int): Custom latency in milliseconds
     *   - kafka_lag (int): Custom Kafka lag value
     * 
     * Returns:
     *   - 200 OK: Service healthy
     *   - 503 Service Unavailable: Service degraded
     * 
     * Example:
     *   curl http://localhost:8080/health
     *   curl http://localhost:8080/health?fail=true
     */
    @GetMapping("/health")
    public ResponseEntity<HealthResponse> health(
            @RequestParam(required = false, defaultValue = "false") boolean fail,
            @RequestParam(required = false) Integer latency,
            @RequestParam(required = false) Integer kafka_lag
    ) {
        HealthResponse response = new HealthResponse();
        response.setTimestamp(Instant.now().toString());
        response.setService("user-api");

        if (fail) {
            // Simulate degraded state
            response.setStatus("degraded");
            
            // Simulate high latency (800ms to 2500ms)
            int simulatedLatency = latency != null ? latency : 
                ThreadLocalRandom.current().nextInt(800, 2500);
            simulateLatency(simulatedLatency);
            response.setLatencyMs(simulatedLatency);

            // Simulate high Kafka lag (5000 to 15000 messages)
            int simulatedKafkaLag = kafka_lag != null ? kafka_lag :
                ThreadLocalRandom.current().nextInt(5000, 15000);
            response.setKafkaLag(simulatedKafkaLag);

            // Elevated error rate
            response.setErrorRate(ThreadLocalRandom.current().nextDouble(0.05, 0.15));
            
            response.setMessage("Service experiencing high latency and Kafka consumer lag");

            // Update metrics for BigQuery export
            metricsSimulator.recordMetric(simulatedLatency, simulatedKafkaLag, response.getErrorRate());
            
            // Write to BigQuery immediately (continuous metrics stream)
            bigQueryWriter.writeMetric(response);

            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
        } else {
            // Normal operation
            response.setStatus("healthy");
            
            // Normal latency (50ms to 200ms)
            int normalLatency = latency != null ? latency :
                ThreadLocalRandom.current().nextInt(50, 200);
            simulateLatency(normalLatency);
            response.setLatencyMs(normalLatency);

            // Low Kafka lag (0 to 1000 messages)
            int normalKafkaLag = kafka_lag != null ? kafka_lag :
                ThreadLocalRandom.current().nextInt(0, 1000);
            response.setKafkaLag(normalKafkaLag);

            // Low error rate
            response.setErrorRate(ThreadLocalRandom.current().nextDouble(0.0, 0.02));
            
            response.setMessage("Service operating normally");

            // Update metrics
            metricsSimulator.recordMetric(normalLatency, normalKafkaLag, response.getErrorRate());
            
            // Write to BigQuery immediately (continuous metrics stream)
            bigQueryWriter.writeMetric(response);

            return ResponseEntity.ok(response);
        }
    }

    /**
     * Chaos engineering endpoint - manually inject failures.
     * 
     * POST /health/inject
     * Body: {
     *   "duration_seconds": 60,
     *   "failure_type": "latency_spike",
     *   "severity": "high"
     * }
     * 
     * This simulates controlled chaos engineering experiments
     * (e.g., "What happens if payment-service has 2s latency for 5 minutes?")
     */
    @PostMapping("/health/inject")
    public ResponseEntity<Map<String, Object>> injectFailure(
            @RequestBody Map<String, Object> request
    ) {
        int duration = (int) request.getOrDefault("duration_seconds", 60);
        String failureType = (String) request.getOrDefault("failure_type", "latency_spike");
        String severity = (String) request.getOrDefault("severity", "medium");

        Map<String, Object> response = new HashMap<>();
        response.put("message", String.format("Injected %s failure (%s severity) for %d seconds", 
            failureType, severity, duration));
        response.put("timestamp", Instant.now().toString());
        response.put("auto_resolve_at", Instant.now().plusSeconds(duration).toString());

        // In a real system, this would trigger a background thread to inject failures
        // For demo purposes, we'll just return confirmation
        metricsSimulator.setFailureMode(true, duration);

        return ResponseEntity.ok(response);
    }

    /**
     * Metrics export endpoint (Prometheus format).
     * 
     * GET /metrics
     * 
     * Returns current metrics for scraping by Prometheus/Cloud Monitoring.
     */
    @GetMapping("/metrics")
    public ResponseEntity<Map<String, Object>> metrics() {
        Map<String, Object> metrics = new HashMap<>();
        
        MetricsSimulator.ServiceMetrics current = metricsSimulator.getCurrentMetrics();
        
        metrics.put("latency_ms", current.getLatencyMs());
        metrics.put("kafka_lag", current.getKafkaLag());
        metrics.put("error_rate", current.getErrorRate());
        metrics.put("cpu_usage", current.getCpuUsage());
        metrics.put("memory_usage", current.getMemoryUsage());
        metrics.put("request_count", current.getRequestCount());
        metrics.put("timestamp", Instant.now().toString());

        return ResponseEntity.ok(metrics);
    }

    /**
     * Cloud Run startup probe endpoint.
     * 
     * GET /startup
     * 
     * Used by Cloud Run to determine when the service is ready to receive traffic.
     */
    @GetMapping("/startup")
    public ResponseEntity<Map<String, String>> startup() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "ready");
        response.put("service", "user-api");
        return ResponseEntity.ok(response);
    }

    /**
     * Cloud Run liveness probe endpoint.
     * 
     * GET /liveness
     * 
     * Used by Cloud Run to determine if the service should be restarted.
     */
    @GetMapping("/liveness")
    public ResponseEntity<Map<String, String>> liveness() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "alive");
        return ResponseEntity.ok(response);
    }

    /**
     * Simulate processing latency by sleeping.
     * 
     * In a real microservice, this latency would come from:
     * - Database queries
     * - External API calls
     * - CPU-intensive computations
     * - Lock contention
     */
    private void simulateLatency(int milliseconds) {
        try {
            Thread.sleep(milliseconds);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}

