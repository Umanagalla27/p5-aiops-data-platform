from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from src.anomaly_detector import AnomalyAlert

# --- Domain Data Models ---


class DeploymentEvent(BaseModel):
    commit_sha: str
    service_name: str
    author: str
    message: str
    deployed_at: str


class IncidentReport(BaseModel):
    incident_id: str
    service_name: str
    severity: Literal["P1", "P2", "P3", "P4"]
    root_cause_summary: str
    evidence_trail: list[str]
    recommended_mitigation: str
    automated_runbook_available: bool


# Mock observability databases
MOCK_DEPLOYMENTS = [
    DeploymentEvent(
        commit_sha="a7b8c9d",
        service_name="rag-retrieval",
        author="dev_lead",
        message="feat: updated cross-encoder reranker batch size to 128",
        deployed_at="10 minutes before anomaly",
    )
]

MOCK_LOGS = {
    "rag-retrieval": [
        "INFO: Processing request batch.",
        "WARN: Memory utilization above 85%.",
        "ERROR: CUDA Out Of Memory while allocating 2.5GB for cross-encoder attention tensor.",
    ],
    "db-writer": [
        "INFO: Connection pool healthy.",
        "FATAL: Database connection timeout after 30000ms. Max connections reached (100/100).",
    ],
}


# --- Agent State Schema ---


class RCAState(TypedDict):
    alert: AnomalyAlert
    incident_severity: Literal["P1", "P2", "P3", "P4"]
    correlated_logs: list[str]
    correlated_deployment: DeploymentEvent | None
    incident_report: IncidentReport | None


# --- Agent Nodes ---


def alert_triage_node(state: RCAState) -> dict:
    """Classifies incident severity (P1-P4) based on anomaly severity and service impact."""
    alert = state["alert"]

    if alert.severity == "CRITICAL" or alert.service_name in ["api-gateway", "auth-service"]:
        sev = "P1"
    elif alert.severity == "HIGH":
        sev = "P2"
    else:
        sev = "P3"

    print(f"\n[RCA Agent] Triaged alert on '{alert.service_name}' as {sev} incident.")
    return {"incident_severity": sev}


def log_correlation_node(state: RCAState) -> dict:
    """Searches application log traces for error keywords matching the anomaly timestamp."""
    svc = state["alert"].service_name
    logs = MOCK_LOGS.get(svc, ["No explicit error logs found."])

    # Filter for warnings and errors
    relevant_logs = [line for line in logs if "WARN" in line or "ERROR" in line or "FATAL" in line]
    print(f"[RCA Agent] Correlated {len(relevant_logs)} error logs from service logs.")
    return {"correlated_logs": relevant_logs}


def deployment_correlation_node(state: RCAState) -> dict:
    """Checks recent CI/CD deployments to correlate code changes with the outage."""
    svc = state["alert"].service_name
    recent_deploy = next((d for d in MOCK_DEPLOYMENTS if d.service_name == svc), None)

    if recent_deploy:
        print(
            "[RCA Agent] Correlated recent code deployment: commit "
            f"{recent_deploy.commit_sha} by {recent_deploy.author}."
        )
    else:
        print("[RCA Agent] No recent deployments found for this service.")

    return {"correlated_deployment": recent_deploy}


def rca_synthesis_node(state: RCAState) -> dict:
    """Synthesizes all observability signals into an actionable Incident Report."""
    alert = state["alert"]
    sev = state["incident_severity"]
    logs = state.get("correlated_logs", [])
    deploy = state.get("correlated_deployment")

    evidence = [
        f"Metric Anomaly: {alert.anomaly_type} ({alert.description})",
    ]
    if logs:
        evidence.append(f"Matching Log Signature: '{logs[-1]}'")
    if deploy:
        evidence.append(
            f"Recent Deployment: Commit {deploy.commit_sha} "
            f"('{deploy.message}') deployed {deploy.deployed_at}"
        )

    # Determine root cause and remediation
    if (
        deploy
        and "batch size" in deploy.message.lower()
        and any("memory" in line.lower() for line in logs)
    ):
        root_cause = (
            f"Recent deployment ({deploy.commit_sha}) increased batch size beyond GPU memory "
            f"limits, causing {alert.service_name} to crash with out-of-memory errors."
        )
        mitigation = f"Rollback deployment to commit prior to {deploy.commit_sha} and restart pod."
        runbook = True
    elif any("timeout" in line.lower() for line in logs):
        root_cause = "Database connection pool exhaustion leading to cascading request timeouts."
        mitigation = "Increase max connection pool limit and terminate idle connection leaks."
        runbook = True
    else:
        root_cause = f"Unusual traffic surge causing {alert.anomaly_type}."
        mitigation = "Scale horizontal pod autoscaler (HPA) to add 2 additional replicas."
        runbook = False

    report = IncidentReport(
        incident_id=f"INC-{abs(hash(alert.timestamp)) % 10000}",
        service_name=alert.service_name,
        severity=sev,
        root_cause_summary=root_cause,
        evidence_trail=evidence,
        recommended_mitigation=mitigation,
        automated_runbook_available=runbook,
    )

    return {"incident_report": report}


# --- Graph Construction ---


def build_rca_graph():
    workflow = StateGraph(RCAState)

    workflow.add_node("alert_triage_node", alert_triage_node)
    workflow.add_node("log_correlation_node", log_correlation_node)
    workflow.add_node("deployment_correlation_node", deployment_correlation_node)
    workflow.add_node("rca_synthesis_node", rca_synthesis_node)

    workflow.add_edge(START, "alert_triage_node")
    workflow.add_edge("alert_triage_node", "log_correlation_node")
    workflow.add_edge("log_correlation_node", "deployment_correlation_node")
    workflow.add_edge("deployment_correlation_node", "rca_synthesis_node")
    workflow.add_edge("rca_synthesis_node", END)

    return workflow.compile()
