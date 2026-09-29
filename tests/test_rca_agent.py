from src.agents.rca_agent import build_rca_graph
from src.anomaly_detector import AnomalyAlert


def test_rca_agent_diagnoses_deployment_oom():
    app = build_rca_graph()

    alert = AnomalyAlert(
        timestamp="2026-09-29T22:30:00Z",
        service_name="rag-retrieval",
        anomaly_type="STATISTICAL_LATENCY_SPIKE",
        severity="CRITICAL",
        metric_value=3500.0,
        baseline_threshold=45.0,
        description="Latency 3500ms exceeded baseline by 15σ",
    )

    initial_state = {
        "alert": alert,
        "incident_severity": "P3",
        "correlated_logs": [],
        "correlated_deployment": None,
        "incident_report": None,
    }

    final_state = app.invoke(initial_state)
    report = final_state["incident_report"]

    assert report is not None
    assert report.severity == "P1"  # Critical alert promoted to P1
    assert "batch size" in report.root_cause_summary.lower()
    assert report.automated_runbook_available is True
    assert len(report.evidence_trail) == 3


def test_rca_agent_diagnoses_connection_exhaustion():
    app = build_rca_graph()

    alert = AnomalyAlert(
        timestamp="2026-09-29T22:35:00Z",
        service_name="db-writer",
        anomaly_type="MULTIVARIATE_SYSTEM_FAULT",
        severity="HIGH",
        metric_value=503.0,
        baseline_threshold=200.0,
        description="Status Code 503 detected",
    )

    initial_state = {
        "alert": alert,
        "incident_severity": "P3",
        "correlated_logs": [],
        "correlated_deployment": None,
        "incident_report": None,
    }

    final_state = app.invoke(initial_state)
    report = final_state["incident_report"]

    assert report is not None
    assert "connection pool" in report.root_cause_summary.lower()
