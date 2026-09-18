from datetime import datetime
from typing import Dict, Any, Union, Optional
from app.detection.models_domain import TelemetryPoint


class TelemetryIngestor:
    """Parses and standardizes incoming telemetry payloads into TelemetryPoint domain objects."""

    @staticmethod
    def ingest(data: Union[Dict[str, Any], TelemetryPoint]) -> TelemetryPoint:
        if isinstance(data, TelemetryPoint):
            return data

        timestamp_raw = data.get("timestamp")
        if isinstance(timestamp_raw, str):
            try:
                dt = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.utcnow()
        elif isinstance(timestamp_raw, datetime):
            dt = timestamp_raw
        else:
            dt = datetime.utcnow()

        return TelemetryPoint(
            lat=float(data.get("lat", data.get("current_lat", 0.0))),
            lng=float(data.get("lng", data.get("current_lng", 0.0))),
            timestamp=dt,
            speed_kmh=float(data.get("speed_kmh", 0.0)),
            heading_degrees=float(data["heading_degrees"]) if data.get("heading_degrees") is not None else None,
            gps_accuracy_meters=float(data.get("gps_accuracy_meters", 10.0)),
            ble_gateway_id=data.get("ble_gateway_id"),
            tracking_available=bool(data.get("tracking_available", True)),
        )
