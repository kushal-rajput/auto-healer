# Sample Metrics Data

These synthetic time-series samples mirror the signals the Auto-Healer consumes from BigQuery. Use them to seed demos, validate anomaly thresholds, or train predictive components.

---

## 1. Schema Reference
| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | TIMESTAMP | UTC time the datapoint was collected. |
| `service_id` | STRING | Microservice identifier (e.g., `user-api`). |
| `latency_ms` | INT64 | Average response latency for the interval. |
| `kafka_lag` | INT64 | Simulated queue lag (messages). |
| `error_rate` | FLOAT64 | Fraction of failed requests (0–1). |
| `cpu_usage` | FLOAT64 | Utilization (0–1). |
| `memory_usage` | FLOAT64 | Utilization (0–1). |
| `status` | STRING | Health label (`OK`, `DEGRADED`, `CRITICAL`). |

These fields align with `bnb-marathon-478505.bnb_autohealer.metrics`.

---

## 2. Baseline vs. Degraded Window
```json
[
  {"timestamp": "2025-11-17T10:00:00Z","service_id":"user-api","latency_ms":45,"kafka_lag":12,"error_rate":0.004,"cpu_usage":0.42,"memory_usage":0.61,"status":"OK"},
  {"timestamp": "2025-11-17T10:01:00Z","service_id":"user-api","latency_ms":52,"kafka_lag":15,"error_rate":0.006,"cpu_usage":0.48,"memory_usage":0.63,"status":"OK"},
  {"timestamp": "2025-11-17T10:02:00Z","service_id":"user-api","latency_ms":1900,"kafka_lag":8000,"error_rate":0.082,"cpu_usage":0.86,"memory_usage":0.91,"status":"DEGRADED"},
  {"timestamp": "2025-11-17T10:03:00Z","service_id":"user-api","latency_ms":2100,"kafka_lag":9200,"error_rate":0.097,"cpu_usage":0.89,"memory_usage":0.94,"status":"CRITICAL"},
  {"timestamp": "2025-11-17T10:04:00Z","service_id":"user-api","latency_ms":65,"kafka_lag":20,"error_rate":0.005,"cpu_usage":0.44,"memory_usage":0.62,"status":"OK"}
]
```
Interpretation:
- Rows 1–2: Healthy baseline feeding Detector agent for comparison.
- Rows 3–4: Violations that trip latency, kafka lag, error rate, CPU, and memory thresholds simultaneously.
- Row 5: Post-healing snapshot verifying recovery.

---

## 3. CSV Snippet (Ready for `bq load`)
```
timestamp,service_id,latency_ms,kafka_lag,error_rate,cpu_usage,memory_usage,status
2025-11-17T10:00:00Z,user-api,45,12,0.004,0.42,0.61,OK
2025-11-17T10:01:00Z,user-api,52,15,0.006,0.48,0.63,OK
2025-11-17T10:02:00Z,user-api,1900,8000,0.082,0.86,0.91,DEGRADED
2025-11-17T10:03:00Z,user-api,2100,9200,0.097,0.89,0.94,CRITICAL
2025-11-17T10:04:00Z,user-api,65,20,0.005,0.44,0.62,OK
```
Load command:
```
bq load --source_format=CSV \
  bnb-marathon-478505:bnb_autohealer.metrics \
  metrics_sample.csv
```

---

## 4. Usage Tips
- Append data every minute to mimic streaming inserts (`python setup_bigquery.py --seed` can be extended with this payload).
- Toggle `/health?fail=true` in the mock service to generate similar spikes in real time.
- When testing Gemini prompts, pass both the violations and the numeric metrics from this set to ensure consistent recommendations.

---

These samples pair with the narrative in `docs/01_idea_overview.md` and the architecture in `HLD_SUBMISSION.md`.