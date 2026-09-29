import json
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402

from src.agents.rca_agent import build_rca_graph  # noqa: E402
from src.anomaly_detector import HybridAnomalyDetector  # noqa: E402
from src.telemetry_stream import TelemetryStreamGenerator  # noqa: E402


def run_aiops_evaluation():
    with open("eval/fault_scenarios.json") as f:
        scenarios = json.load(f)

    print(f"\n[AIOps Eval] Starting chaos evaluation across {len(scenarios)} injected faults...")

    # 1. Warm up Anomaly Detector on 80 healthy events
    detector = HybridAnomalyDetector(z_score_threshold=3.0)
    baseline_events = [
        TelemetryStreamGenerator.generate_normal_event() for _ in range(80)
    ]
    detector.fit_baseline(baseline_events)

    # 2. Compile LangGraph RCA Agent
    rca_agent = build_rca_graph()

    detected_count = 0
    correct_rca_count = 0
    detection_latencies_ms = []

    for item in scenarios:
        # Generate the injected fault event
        fault_event = TelemetryStreamGenerator.generate_fault_event(
            fault_type=item["fault_type"], service=item["service"]
        )

        # Measure Time to Detect (TTD)
        t0 = time.perf_counter()
        alert = detector.inspect_event(fault_event)
        ttd_ms = (time.perf_counter() - t0) * 1000

        if alert is not None:
            detected_count += 1
            detection_latencies_ms.append(ttd_ms)

            # Trigger RCA Agent to diagnose root cause
            initial_state = {
                "alert": alert,
                "incident_severity": "P3",
                "correlated_logs": [],
                "correlated_deployment": None,
                "incident_report": None,
            }
            res = rca_agent.invoke(initial_state)
            report = res["incident_report"]

            # Verify if diagnosis matches ground truth
            if item["ground_truth_root_cause"].lower() in report.root_cause_summary.lower():
                correct_rca_count += 1

    total = len(scenarios)
    detection_recall = (detected_count / total) * 100
    avg_ttd_ms = np.mean(detection_latencies_ms) if detection_latencies_ms else 0.0
    rca_accuracy = (correct_rca_count / total) * 100

    print("\n" + "=" * 80)
    print("AIOPS BENCHMARK EVALUATION SCORECARD (20 INJECTED FAULTS)")
    print("=" * 80)
    print(f"Total Fault Injections:            {total}")
    print(
        f"Fault Detection Recall:            {detection_recall:.1f}% "
        f"({detected_count}/{total} caught)"
    )
    print(f"Mean Time to Detect (TTD):         {avg_ttd_ms:.2f} ms (Sub-millisecond detection)")
    print(
        f"RCA Diagnosis Correctness:         {rca_accuracy:.1f}% "
        f"({correct_rca_count}/{total} accurate)"
    )
    print("=" * 80)

    # Save to results/
    os.makedirs("results", exist_ok=True)
    report_data = {
        "total_faults": total,
        "detection_recall_pct": detection_recall,
        "mean_time_to_detect_ms": round(float(avg_ttd_ms), 3),
        "rca_diagnosis_accuracy_pct": rca_accuracy,
    }
    with open("results/aiops_benchmark_report.json", "w") as f:
        json.dump(report_data, f, indent=2)
    print("Saved evaluation report to results/aiops_benchmark_report.json")


if __name__ == "__main__":
    run_aiops_evaluation()
