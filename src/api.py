import time

from fastapi import FastAPI
from pydantic import BaseModel

from src.agents.rca_agent import IncidentReport, build_rca_graph
from src.anomaly_detector import HybridAnomalyDetector
from src.telemetry_stream import ServiceMetricEvent, TelemetryStreamGenerator

app = FastAPI(
    title="P5 AIOps Incident & Observability API",
    description="Real-Time Anomaly Detection, Automated LangGraph RCA, and SRE Incident Triage",
    version="1.0.0",
)

# Global engines
detector = HybridAnomalyDetector(z_score_threshold=3.0)
rca_agent = build_rca_graph()
active_incidents: list[IncidentReport] = []


@app.on_event("startup")
def startup_event():
    print("[API] Fitting Anomaly Detector baseline on healthy events...")
    baseline = [TelemetryStreamGenerator.generate_normal_event() for _ in range(60)]
    detector.fit_baseline(baseline)


class TelemetryIngestRequest(BaseModel):
    service_name: str
    endpoint: str
    cpu_percent: float
    memory_percent: float
    latency_ms: float
    status_code: int = 200


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "anomaly_detector_ready": detector.is_fitted,
        "active_incidents_count": len(active_incidents),
    }


@app.post("/v1/telemetry/ingest")
def ingest_telemetry_event(req: TelemetryIngestRequest):
    event = ServiceMetricEvent(
        timestamp=str(time.time()),
        service_name=req.service_name,
        endpoint=req.endpoint,
        cpu_percent=req.cpu_percent,
        memory_percent=req.memory_percent,
        latency_ms=req.latency_ms,
        status_code=req.status_code,
    )

    # 1. Run Anomaly Detection
    alert = detector.inspect_event(event)

    if alert is None:
        return {"status": "NORMAL", "anomaly_detected": False}

    # 2. Anomaly Detected: Run LangGraph RCA Agent
    rca_result = rca_agent.invoke(
        {
            "alert": alert,
            "incident_severity": "P3",
            "correlated_logs": [],
            "correlated_deployment": None,
            "incident_report": None,
        }
    )

    report = rca_result["incident_report"]
    active_incidents.append(report)

    return {
        "status": "ANOMALY_DETECTED",
        "anomaly_type": alert.anomaly_type,
        "incident_report": report.dict(),
    }


@app.get("/v1/incidents/active")
def list_active_incidents():
    return {"active_incidents": [inc.dict() for inc in active_incidents[-10:]]}
