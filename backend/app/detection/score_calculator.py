from app.detection.models_domain import TelemetryPoint, ExpectedJourney, SystemContext
from app.detection.config import DetectionConfig, DEFAULT_CONFIG


class ScoreCalculator:
    """Calculates evidence-based misplacement score using corridor deviation, heading mismatch, and unbind state."""

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config

    def calculate_score(
        self,
        dist_nearest_valid_km: float,
        heading_diff_deg: float,
        telemetry: TelemetryPoint,
        journey: ExpectedJourney,
        context: SystemContext,
    ) -> float:
        """
        Calculates composite misplacement score (0.0 to 1.0):
            S_corridor = min(1.0, dist_nearest_valid_km / 30.0)
            S_heading  = min(1.0, heading_diff_deg / 90.0) or 0.0 if speed <= 20 km/h
            S_unbind   = 1.0 if ble_gateway != assigned_vehicle and not transfer_active else 0.0
            composite_score = 0.40*S_corridor + 0.35*S_heading + 0.25*S_unbind
        """
        # 1. Corridor deviation score
        s_corridor = min(1.0, max(0.0, dist_nearest_valid_km / self.config.score_normalizer_corridor_km))

        # 2. Heading deviation score (ignored if speed <= 20 km/h)
        if telemetry.speed_kmh <= self.config.low_speed_cutoff_kmh:
            s_heading = 0.0
        else:
            s_heading = min(1.0, max(0.0, heading_diff_deg / self.config.score_normalizer_heading_deg))

        # 3. Unbind score (BLE gateway mismatch vs assigned vehicle)
        s_unbind = 0.0
        if telemetry.ble_gateway_id and journey.vehicle_code:
            # If gateway differs from vehicle and no active vehicle transfer
            if (
                telemetry.ble_gateway_id != journey.vehicle_code
                and not context.active_vehicle_transfer
            ):
                s_unbind = 1.0

        # Composite weighted sum
        score = (
            self.config.weight_corridor * s_corridor
            + self.config.weight_heading * s_heading
            + self.config.weight_unbind * s_unbind
        )

        return round(min(1.0, max(0.0, score)), 2)
