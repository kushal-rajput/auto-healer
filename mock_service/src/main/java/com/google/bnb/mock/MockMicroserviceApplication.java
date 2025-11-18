package com.google.bnb.mock;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Mock Microservice for Auto-Healer Demo
 * 
 * This Spring Boot application simulates a production microservice with
 * controllable failure modes for testing the AI-Driven Auto-Healer.
 * 
 * Features:
 * - Simulated latency spikes
 * - Mock Kafka consumer lag
 * - Configurable error rates
 * - Cloud Run health check endpoints
 * 
 * BNB Marathon 2025 - Industry Impact Component
 * 
 * @author Kunal Rajput
 * @version 1.0.0
 */
@SpringBootApplication
public class MockMicroserviceApplication {

    public static void main(String[] args) {
        SpringApplication.run(MockMicroserviceApplication.class, args);
    }
}

