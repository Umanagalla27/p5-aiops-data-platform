import random

from src.anomaly_detector import HybridAnomalyDetector
from src.telemetry_stream import TelemetryStreamGenerator


def test_anomaly_detector_catches_latency_spike():
    random.seed(42)
    detector = HybridAnomalyDetector(z_score_threshold=3.0)

    # 1. Feed 60 normal healthy events
    healthy_events = [
        TelemetryStreamGenerator.generate_normal_event("rag-retrieval") for _ in range(60)
    ]
    detector.fit_baseline(healthy_events)

    for e in healthy_events:
        alert = detector.inspect_event(e)
        assert alert is None  # No false alarms on normal traffic

    # 2. Inject massive latency spike
    spike_event = TelemetryStreamGenerator.generate_fault_event(
        "LATENCY_SPIKE", service="rag-retrieval"
    )
    alert = detector.inspect_event(spike_event)

    assert alert is not None
    assert alert.anomaly_type == "STATISTICAL_LATENCY_SPIKE"
    assert alert.service_name == "rag-retrieval"
    assert alert.metric_value >= 1000.0


def test_anomaly_detector_catches_oom_crash():
    detector = HybridAnomalyDetector()
    healthy_events = [
        TelemetryStreamGenerator.generate_normal_event("db-writer") for _ in range(60)
    ]
    detector.fit_baseline(healthy_events)

    oom_event = TelemetryStreamGenerator.generate_fault_event("OOM_CRASH", service="db-writer")
    alert = detector.inspect_event(oom_event)

    assert alert is not None
    assert alert.severity in ["HIGH", "CRITICAL"]
