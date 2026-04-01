"""Lightweight telemetry hooks; expand with OpenTelemetry when OTEL_EXPORTER_OTLP_ENDPOINT is set."""

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_telemetry(settings: Settings | None = None) -> None:
    """Initialize tracing/metrics if configured. No-op by default."""
    settings = settings or get_settings()
    if settings.otel_exporter_otlp_endpoint:
        logger.info(
            "OTEL endpoint configured; add opentelemetry-sdk and instrumentors to enable export",
            extra={"endpoint": settings.otel_exporter_otlp_endpoint},
        )
