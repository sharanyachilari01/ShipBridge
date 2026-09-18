from datetime import datetime
from typing import Optional, List
from app.detection.models_domain import TelemetryPoint
from app.detection.config import DetectionConfig, DEFAULT_CONFIG


class DataValidator:
    """Validates telemetry data quality, coordinate bounds, staleness, and GPS accuracy."""

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config

    @staticmethod
    def is_valid_coordinates(lat: float, lng: float) -> bool:
        if lat == 0.0 and lng == 0.0:
            return False
        return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0

    @staticmethod
    def is_stale_or_duplicate(
        current_point: TelemetryPoint, history: List[TelemetryPoint]
    ) -> bool:
        if not history:
            return False
        latest = history[-1]
        # Duplicate or backwards timestamp
        if current_point.timestamp <= latest.timestamp:
            return True
        return False

    def is_gps_accuracy_valid(self, point: TelemetryPoint) -> bool:
        return point.gps_accuracy_meters <= self.config.max_gps_accuracy_meters
