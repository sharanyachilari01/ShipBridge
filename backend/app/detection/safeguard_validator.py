from datetime import datetime
from typing import Optional
from app.detection.models_domain import (
    TelemetryPoint,
    ExpectedJourney,
    SystemContext,
    SafeguardOutcomes,
)
from app.detection.config import DetectionConfig, DEFAULT_CONFIG


class SafeguardValidator:
    """Evaluates all 7 false-positive safeguards before misplacement decision."""

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config

    def evaluate(
        self,
        telemetry: Optional[TelemetryPoint],
        journey: ExpectedJourney,
        context: SystemContext,
        dist_nearest_valid_km: float,
        on_alt_route: bool,
        now: datetime,
    ) -> SafeguardOutcomes:
        outcomes = SafeguardOutcomes()

        # Safeguard 1: Approved Reroute
        outcomes.approved_reroute_present = context.approved_reroute_active

        # Safeguard 2: Active Vehicle Transfer (within 15-min grace period)
        if context.active_vehicle_transfer and context.transfer_started_at:
            minutes_elapsed = (now - context.transfer_started_at).total_seconds() / 60.0
            if minutes_elapsed <= self.config.vehicle_transfer_grace_minutes:
                outcomes.vehicle_transfer_active = True
        elif context.active_vehicle_transfer:
            outcomes.vehicle_transfer_active = True

        # Safeguard 3: Traffic Delay Only (late while still on a valid route <= 15km)
        is_late = False
        if journey.delivery_deadline and now > journey.delivery_deadline:
            is_late = True
        elif journey.expected_arrival_time and now > journey.expected_arrival_time:
            is_late = True

        if is_late and dist_nearest_valid_km <= self.config.max_off_route_distance_km:
            outcomes.traffic_delay_only = True

        # Safeguard 4: Signal Loss Only
        if telemetry is None or not telemetry.tracking_available:
            outcomes.signal_loss_only = True
        elif (now - telemetry.timestamp).total_seconds() / 3600.0 >= self.config.signal_loss_threshold_hours:
            outcomes.signal_loss_only = True

        # Safeguard 5: GPS Accuracy Valid
        if telemetry is not None:
            outcomes.gps_accuracy_valid = telemetry.gps_accuracy_meters <= self.config.max_gps_accuracy_meters
        else:
            outcomes.gps_accuracy_valid = False

        # Safeguard 6: Allowed Alternative Route
        outcomes.on_allowed_alternative_route = on_alt_route or (dist_nearest_valid_km <= self.config.max_off_route_distance_km)

        # Safeguard 7: Low Speed Heading Ignored
        if telemetry is not None and telemetry.speed_kmh <= self.config.low_speed_cutoff_kmh:
            outcomes.low_speed_heading_ignored = True

        return outcomes
