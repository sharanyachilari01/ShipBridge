from datetime import datetime, timedelta
from typing import Optional, List
from app.detection.models_domain import TelemetryPoint
from app.detection.config import DetectionConfig, DEFAULT_CONFIG


class Tier1Sentry:
    """Fast-triage sentry checking signal loss, missing telemetry, or disabled tracking."""

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config

    def check_signal_status(
        self, current_point: Optional[TelemetryPoint], now: datetime
    ) -> Optional[str]:
        """
        Returns 'UNKNOWN_SIGNAL_MONITOR' if tracking is unavailable or missing for > signal_loss_threshold_hours.
        Returns None if telemetry signal is active and timely.
        """
        if current_point is None:
            return "UNKNOWN_SIGNAL_MONITOR"

        if not current_point.tracking_available:
            return "UNKNOWN_SIGNAL_MONITOR"

        time_gap_hours = (now - current_point.timestamp).total_seconds() / 3600.0
        if time_gap_hours >= self.config.signal_loss_threshold_hours:
            return "UNKNOWN_SIGNAL_MONITOR"

        return None
