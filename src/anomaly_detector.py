from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from src.telemetry_stream import ServiceMetricEvent


@dataclass
class AnomalyAlert:
    timestamp: str
    service_name: str
    anomaly_type: str
    severity: str
    metric_value: float
    baseline_threshold: float
    description: str


class HybridAnomalyDetector:
    def __init__(self, z_score_threshold: float = 3.0):
        self.z_score_threshold = z_score_threshold
        # Unsupervised Isolation Forest for multivariate anomaly detection
        self.iso_forest = IsolationForest(n_estimators=100, contamination=0.03, random_state=42)
        self.is_fitted = False
        self.history_latency: list[float] = []

    def fit_baseline(self, historical_events: list[ServiceMetricEvent]):
        """Trains baseline distribution on healthy historical metrics."""
        features = [
            [e.cpu_percent, e.memory_percent, e.latency_ms, 1 if e.status_code >= 500 else 0]
            for e in historical_events
        ]
        self.iso_forest.fit(features)
        self.history_latency = [e.latency_ms for e in historical_events]
        self.is_fitted = True
        print(f"[Detector] Baseline fitted on {len(historical_events)} healthy events.")

    def inspect_event(self, event: ServiceMetricEvent) -> AnomalyAlert | None:
        """Inspects single incoming telemetry event in real time."""
        # 1. Statistical Z-Score Check (Latency)
        if len(self.history_latency) >= 20:
            mean = np.mean(self.history_latency[-50:])
            std = np.std(self.history_latency[-50:]) or 1.0
            z_score = (event.latency_ms - mean) / std

            if z_score >= self.z_score_threshold:
                return AnomalyAlert(
                    timestamp=event.timestamp,
                    service_name=event.service_name,
                    anomaly_type="STATISTICAL_LATENCY_SPIKE",
                    severity="CRITICAL" if z_score > 5.0 else "WARNING",
                    metric_value=event.latency_ms,
                    baseline_threshold=round(float(mean + self.z_score_threshold * std), 2),
                    description=(
                        f"Latency {event.latency_ms}ms exceeded baseline "
                        f"{mean:.1f}ms by {z_score:.1f}σ"
                    ),
                )

        # 2. Multivariate Isolation Forest Check
        if self.is_fitted:
            features = [
                [
                    event.cpu_percent,
                    event.memory_percent,
                    event.latency_ms,
                    1 if event.status_code >= 500 else 0,
                ]
            ]
            # IsolationForest returns -1 for anomalies, 1 for inliers
            prediction = self.iso_forest.predict(features)[0]
            if prediction == -1 and event.status_code >= 500:
                return AnomalyAlert(
                    timestamp=event.timestamp,
                    service_name=event.service_name,
                    anomaly_type="MULTIVARIATE_SYSTEM_FAULT",
                    severity="HIGH",
                    metric_value=float(event.status_code),
                    baseline_threshold=200.0,
                    description=(
                        "Unusual multivariate anomaly detected with "
                        f"Status Code {event.status_code}"
                    ),
                )

        # Update sliding window
        self.history_latency.append(event.latency_ms)
        return None
