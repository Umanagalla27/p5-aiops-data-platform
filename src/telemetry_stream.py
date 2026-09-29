import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass
class ServiceMetricEvent:
    timestamp: str
    service_name: str
    endpoint: str
    cpu_percent: float
    memory_percent: float
    latency_ms: float
    status_code: int
    is_fault_injected: bool = False


class TelemetryStreamGenerator:
    SERVICES = ["api-gateway", "auth-service", "rag-retrieval", "db-writer"]
    ENDPOINTS = {
        "api-gateway": ["/v1/query", "/health", "/v1/submit"],
        "auth-service": ["/oauth/token", "/verify"],
        "rag-retrieval": ["/search/dense", "/rerank"],
        "db-writer": ["/insert", "/update"],
    }

    @classmethod
    def generate_normal_event(cls, service: str | None = None) -> ServiceMetricEvent:
        svc = service or random.choice(cls.SERVICES)
        ep = random.choice(cls.ENDPOINTS[svc])

        return ServiceMetricEvent(
            timestamp=datetime.now(UTC).isoformat(),
            service_name=svc,
            endpoint=ep,
            cpu_percent=round(random.uniform(15.0, 45.0), 2),
            memory_percent=round(random.uniform(30.0, 55.0), 2),
            latency_ms=round(random.gauss(45.0, 10.0), 2),  # Normal distribution around 45ms
            status_code=200 if random.random() > 0.02 else 500,  # 2% baseline noise
            is_fault_injected=False,
        )

    @classmethod
    def generate_fault_event(
        cls, fault_type: str = "LATENCY_SPIKE", service: str = "rag-retrieval"
    ) -> ServiceMetricEvent:
        """Injects controlled infrastructure anomalies for testing detection engines."""
        ep = random.choice(cls.ENDPOINTS[service])

        if fault_type == "LATENCY_SPIKE":
            return ServiceMetricEvent(
                timestamp=datetime.now(UTC).isoformat(),
                service_name=service,
                endpoint=ep,
                cpu_percent=round(random.uniform(75.0, 95.0), 2),
                memory_percent=round(random.uniform(50.0, 65.0), 2),
                latency_ms=round(random.uniform(1200.0, 4500.0), 2),  # Massive spike
                status_code=200,
                is_fault_injected=True,
            )
        elif fault_type == "OOM_CRASH":
            return ServiceMetricEvent(
                timestamp=datetime.now(UTC).isoformat(),
                service_name=service,
                endpoint=ep,
                cpu_percent=round(random.uniform(90.0, 99.0), 2),
                memory_percent=round(random.uniform(92.0, 98.5), 2),
                latency_ms=round(random.uniform(800.0, 2000.0), 2),
                status_code=503,  # Service unavailable
                is_fault_injected=True,
            )
        else:  # ERROR_BURST
            return ServiceMetricEvent(
                timestamp=datetime.now(UTC).isoformat(),
                service_name=service,
                endpoint=ep,
                cpu_percent=round(random.uniform(40.0, 60.0), 2),
                memory_percent=round(random.uniform(40.0, 50.0), 2),
                latency_ms=round(random.uniform(150.0, 300.0), 2),
                status_code=500,  # Internal server error
                is_fault_injected=True,
            )


if __name__ == "__main__":
    print("[Telemetry] Generating 5 normal events and 1 injected fault:")
    for _ in range(5):
        print(asdict(TelemetryStreamGenerator.generate_normal_event()))
    print("\nFAULT INJECTION:")
    print(asdict(TelemetryStreamGenerator.generate_fault_event("LATENCY_SPIKE")))
