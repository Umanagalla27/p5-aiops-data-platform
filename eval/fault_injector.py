import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.telemetry_stream import TelemetryStreamGenerator  # noqa: E402


def generate_20_fault_scenarios():
    """Generates 20 challenging infrastructure fault scenarios mapped to ground-truth root causes."""
    scenarios = []

    # 1. 7 Latency Spikes
    for i in range(1, 8):
        scenarios.append(
            {
                "id": f"fault-lat-{i}",
                "fault_type": "LATENCY_SPIKE",
                "service": "rag-retrieval",
                "expected_anomaly": "STATISTICAL_LATENCY_SPIKE",
                "expected_severity": "P1",
                "ground_truth_root_cause": "increased batch size beyond GPU memory limits",
            }
        )

    # 2. 7 Connection / Error Bursts
    for i in range(1, 8):
        scenarios.append(
            {
                "id": f"fault-err-{i}",
                "fault_type": "ERROR_BURST",
                "service": "db-writer",
                "expected_anomaly": "MULTIVARIATE_SYSTEM_FAULT",
                "expected_severity": "P2",
                "ground_truth_root_cause": "connection pool",
            }
        )

    # 3. 6 OOM Crashes
    for i in range(1, 7):
        scenarios.append(
            {
                "id": f"fault-oom-{i}",
                "fault_type": "OOM_CRASH",
                "service": "rag-retrieval",
                "expected_anomaly": "STATISTICAL_LATENCY_SPIKE",
                "expected_severity": "P1",
                "ground_truth_root_cause": "increased batch size beyond GPU memory limits",
            }
        )

    os.makedirs("eval", exist_ok=True)
    with open("eval/fault_scenarios.json", "w") as f:
        json.dump(scenarios, f, indent=2)

    print(
        f"[Chaos Engineering] Generated {len(scenarios)} fault-injection scenarios "
        "in eval/fault_scenarios.json"
    )


if __name__ == "__main__":
    generate_20_fault_scenarios()
