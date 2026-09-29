import os
import sys
from pathlib import Path

# Add project root to sys.path so running directly works seamlessly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.telemetry_stream import TelemetryStreamGenerator  # noqa: E402


class TelemetryBatchAggregator:
    def __init__(self, output_dir: str = "data/analytics"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_daily_aggregation(self, num_records: int = 5000) -> str:
        """
        Simulates PySpark distributed batch processing over raw daily telemetry logs.
        Aggregates raw latency and error counts into columnar Parquet files.
        """
        print(f"[Data Pipeline] Processing {num_records} raw telemetry logs...")

        records = []
        for _ in range(num_records):
            event = TelemetryStreamGenerator.generate_normal_event()
            records.append(
                {
                    "timestamp": event.timestamp,
                    "service_name": event.service_name,
                    "endpoint": event.endpoint,
                    "cpu_percent": event.cpu_percent,
                    "memory_percent": event.memory_percent,
                    "latency_ms": event.latency_ms,
                    "is_error": 1 if event.status_code >= 500 else 0,
                }
            )

        df = pd.DataFrame(records)

        # PySpark-style GroupBy and Aggregate
        agg_df = (
            df.groupby("service_name")
            .agg(
                total_requests=("latency_ms", "count"),
                p50_latency_ms=("latency_ms", "median"),
                p95_latency_ms=("latency_ms", lambda x: np.percentile(x, 95)),
                p99_latency_ms=("latency_ms", lambda x: np.percentile(x, 99)),
                avg_cpu_percent=("cpu_percent", "mean"),
                avg_memory_percent=("memory_percent", "mean"),
                total_errors=("is_error", "sum"),
            )
            .reset_index()
        )

        # Calculate Availability SLA percentage
        agg_df["availability_sla_pct"] = (
            (agg_df["total_requests"] - agg_df["total_errors"]) / agg_df["total_requests"]
        ) * 100
        agg_df["availability_sla_pct"] = agg_df["availability_sla_pct"].round(3)

        # Save to columnar Parquet format
        parquet_path = os.path.join(self.output_dir, "daily_service_metrics.parquet")
        agg_df.to_parquet(parquet_path, index=False)
        print(f"[Data Pipeline] Saved aggregated metrics to {parquet_path}")

        return parquet_path


if __name__ == "__main__":
    pipeline = TelemetryBatchAggregator()
    path = pipeline.run_daily_aggregation(5000)

    # Read back and display summary
    result_df = pd.read_parquet(path)
    print("\n" + "=" * 80)
    print("DAILY SERVICE RELIABILITY METRICS (PYSPARK AGGREGATION)")
    print("=" * 80)
    print(result_df.to_string(index=False))
    print("=" * 80)
