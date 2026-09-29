import json
import os

import pandas as pd


def test_parquet_batch_analytics_exists():
    """Verifies that daily aggregated Parquet analytics data was generated."""
    parquet_file = os.path.join("data", "analytics", "daily_service_metrics.parquet")
    assert os.path.exists(parquet_file), "Analytics Parquet file missing!"

    df = pd.read_parquet(parquet_file)
    assert len(df) == 4  # 4 services
    assert "availability_sla_pct" in df.columns
    assert "p99_latency_ms" in df.columns


def test_aiops_benchmark_report_thresholds():
    """Asserts that chaos engineering benchmark report achieves >= 95% detection recall."""
    report_file = os.path.join("results", "aiops_benchmark_report.json")
    assert os.path.exists(report_file), "Benchmark report missing!"

    with open(report_file) as f:
        data = json.load(f)

    assert data["detection_recall_pct"] == 100.0, "Detection recall below 100%!"
    assert data["rca_diagnosis_accuracy_pct"] == 100.0, "RCA diagnosis accuracy below 100%!"
    assert data["mean_time_to_detect_ms"] < 5.0, "TTD latency too high!"
