import sys
from pathlib import Path

# Ensure project root is in sys.path when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from src.agents.rca_agent import build_rca_graph  # noqa: E402
from src.anomaly_detector import AnomalyAlert  # noqa: E402


def demo_rca_incident_triage():
    app = build_rca_graph()

    # Simulate alert triggered from Anomaly Detector
    alert = AnomalyAlert(
        timestamp="2026-09-29T22:30:00Z",
        service_name="rag-retrieval",
        anomaly_type="STATISTICAL_LATENCY_SPIKE",
        severity="CRITICAL",
        metric_value=4200.0,
        baseline_threshold=65.0,
        description="Latency 4200ms exceeded 3σ threshold",
    )

    print("\n" + "=" * 70)
    print("STARTING AUTOMATED ROOT CAUSE ANALYSIS (RCA)")
    print("=" * 70)

    result = app.invoke(
        {
            "alert": alert,
            "incident_severity": "P3",
            "correlated_logs": [],
            "correlated_deployment": None,
            "incident_report": None,
        }
    )

    report = result["incident_report"]
    print("\n" + "=" * 70)
    print("GENERATED INCIDENT REPORT (SRE TRIAGE SUMMARY)")
    print("=" * 70)
    print(f"Incident ID:       {report.incident_id}")
    print(f"Service:           {report.service_name}")
    print(f"Severity:          {report.severity}")
    print(f"Root Cause:        {report.root_cause_summary}")
    print(f"Mitigation:        {report.recommended_mitigation}")
    print(f"Auto-Runbook:      {report.automated_runbook_available}")
    print("\nEvidence Trail:")
    for e in report.evidence_trail:
        print(f"  • {e}")
    print("=" * 70)


if __name__ == "__main__":
    demo_rca_incident_triage()
