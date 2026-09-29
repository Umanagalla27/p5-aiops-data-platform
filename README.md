# P5: Production AIOps Assistant & Event Data Platform

[![P5 AIOps CI Pipeline](https://github.com/Umanagalla27/p5-aiops-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Umanagalla27/p5-aiops-data-platform/actions)
![Isolation Forest](https://img.shields.io/badge/ML-Isolation_Forest-FFAA00.svg)
![LangGraph](https://img.shields.io/badge/RCA-LangGraph_StateGraph-34D399.svg?logo=python&logoColor=white)
![Parquet](https://img.shields.io/badge/Data-Columnar_Parquet-13ADC7.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)

An enterprise-grade AIOps platform for distributed microservices. Features **hybrid real-time anomaly detection (Statistical Z-Score + Unsupervised Isolation Forest)**, an automated **LangGraph Root Cause Analysis (RCA) Agent** that correlates metrics with logs and CI/CD code deployments, and a **PySpark-style columnar Parquet analytics engine** with **dbt models** tracking SRE availability SLAs and MTTR.

---

## 🏛️ System Architecture

```text
Microservice Telemetry Stream (CPU, Memory, Latency, Status Codes)
       │
       ▼
┌───────────────────────────┐
│  Hybrid Anomaly Detector  │
│  • Statistical (3.0σ)     │
│  • Isolation Forest (ML)  │
└─────────────┬─────────────┘
              │ (0.11 ms TTD) [Anomaly Detected]
              ▼
┌───────────────────────────┐
│    LangGraph RCA Agent    │
│  1. Severity Triage (P1)  │
│  2. Log Error Match       │
│  3. CI/CD Git Commits     │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ Automated Incident Triage │ ──► Root Cause, Evidence Trail & Runbook
└───────────────────────────┘
```

---

## 📊 Chaos Engineering Benchmark (20 Injected Faults)

Evaluated against a 20-scenario chaos engineering test suite (Latency Spikes, Connection Pool Exhaustion, CUDA OOMs):

| Metric | Score | Production SLA |
|---|---|---|
| **Fault Detection Recall** | **100.0% (20/20)** | $\ge 95.0\%$ |
| **Mean Time to Detect (TTD)** | **0.11 ms** | $< 50\text{ ms}$ (Real-Time) |
| **RCA Diagnosis Correctness** | **100.0% (20/20)** | $\ge 90.0\%$ |
| **Daily Telemetry Batch Rate** | **5,000 logs/sec** | Columnar Parquet Output |

---

## 📈 SRE Reliability & SLA Analytics (dbt + Parquet)

Aggregated daily metrics across microservices:

| Service Name | Total Requests | p50 Latency | p95 Latency | p99 Latency | Availability SLA (%) |
|---|---|---|---|---|---|
| `api-gateway` | 1,242 | 45.6 ms | 61.1 ms | 68.2 ms | **98.87%** |
| `auth-service` | 1,208 | 45.8 ms | 61.2 ms | 66.9 ms | **98.68%** |
| `rag-retrieval`| 1,324 | 45.5 ms | 61.0 ms | 66.7 ms | **97.96%** |
| `db-writer` | 1,226 | 45.3 ms | 61.1 ms | 67.2 ms | **97.23%** |

---

## 🚀 Quick Start

### 1. Run Analytics & Chaos Benchmark
```bash
python src/data/batch_aggregator.py
python eval/run_aiops_eval.py
```

### 2. Start Incident Management API
```bash
uvicorn src.api:app --reload --port 8000
```
