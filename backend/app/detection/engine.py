import time
from datetime import datetime
from typing import Optional, List
from app.detection.models_domain import (
    TelemetryPoint,
    ExpectedJourney,
    SystemContext,
    SafeguardOutcomes,
    DetectionResultDomain,
)
from app.detection.config import DetectionConfig, DEFAULT_CONFIG
from app.detection.telemetry_ingestor import TelemetryIngestor
from app.detection.data_validator import DataValidator
from app.detection.tier1_sentry import Tier1Sentry
from app.detection.route_matcher import RouteMatcher
from app.detection.trajectory_analyzer import TrajectoryAnalyzer
from app.detection.safeguard_validator import SafeguardValidator
from app.detection.score_calculator import ScoreCalculator


class MisplacementDecisionEngine:
    """
    Stage 1 False-Positive-Resistant Misplaced Shipment Detection Engine.
    Orchestrates all independent sub-components to perform evidence-based classification.
    """

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config
        self.data_validator = DataValidator(config)
        self.tier1_sentry = Tier1Sentry(config)
        self.route_matcher = RouteMatcher(config)
        self.trajectory_analyzer = TrajectoryAnalyzer(config)
        self.safeguard_validator = SafeguardValidator(config)
        self.score_calculator = ScoreCalculator(config)

    def evaluate_shipment(
        self,
        journey: ExpectedJourney,
        current_telemetry: Optional[TelemetryPoint],
        telemetry_history: List[TelemetryPoint],
        context: SystemContext,
        now: Optional[datetime] = None,
    ) -> DetectionResultDomain:
        now_dt = now or datetime.utcnow()
        alert_id = f"ALT-{journey.shipment_id}-{int(time.time())}"

        # 1. Check Signal Loss / Missing Telemetry via Tier 1 Sentry
        sentry_status = self.tier1_sentry.check_signal_status(current_telemetry, now_dt)
        if sentry_status == "UNKNOWN_SIGNAL_MONITOR":
            safeguards = SafeguardOutcomes(
                signal_loss_only=True,
                approved_reroute_present=context.approved_reroute_active,
                vehicle_transfer_active=context.active_vehicle_transfer,
            )
            return DetectionResultDomain(
                alert_id=alert_id,
                shipment_id=journey.shipment_id,
                status="UNKNOWN_SIGNAL_MONITOR",
                misplacement_score=0.0,
                location={"lat": 0.0, "lng": 0.0},
                assigned_vehicle=journey.vehicle_code,
                distance_to_primary_route_km=0.0,
                distance_to_nearest_valid_route_km=0.0,
                heading_difference_deg=0.0,
                persistent_anomaly=False,
                safeguard_outcomes=safeguards,
                primary_cause="TELEMETRY_SIGNAL_LOSS",
                explanation=f"Evidence-based classification: Signal for shipment {journey.shipment_id} is missing or stale (> {self.config.signal_loss_threshold_hours}h gap). Placed in monitoring queue.",
                timestamp=now_dt,
            )

        # 2. Ingest & Validate Coordinates
        pt = current_telemetry
        if not self.data_validator.is_valid_coordinates(pt.lat, pt.lng):
            safeguards = SafeguardOutcomes(gps_accuracy_valid=False)
            return DetectionResultDomain(
                alert_id=alert_id,
                shipment_id=journey.shipment_id,
                status="UNKNOWN_SIGNAL_MONITOR",
                misplacement_score=0.0,
                location={"lat": pt.lat, "lng": pt.lng},
                assigned_vehicle=journey.vehicle_code,
                distance_to_primary_route_km=0.0,
                distance_to_nearest_valid_route_km=0.0,
                heading_difference_deg=0.0,
                persistent_anomaly=False,
                safeguard_outcomes=safeguards,
                primary_cause="INVALID_GPS_COORDINATES",
                explanation=f"Evidence-based classification: Invalid coordinate payload ({pt.lat}, {pt.lng}) received for shipment {journey.shipment_id}.",
                timestamp=now_dt,
            )

        # 3. Route Matcher
        dist_primary, dist_nearest_valid, on_alt_route = self.route_matcher.match_location(
            pt.lat, pt.lng, journey
        )

        # 4. Trajectory Analyzer (Persistence & Heading)
        all_points = telemetry_history + [pt] if pt not in telemetry_history else telemetry_history
        persistent_anomaly, consecutive_off_count = self.trajectory_analyzer.evaluate_persistence(
            all_points, journey
        )

        prev_pt = telemetry_history[-1] if len(telemetry_history) >= 1 else None
        heading_diff_deg = self.trajectory_analyzer.compute_heading_difference(pt, prev_pt, 0.0)

        # 5. Safeguard Evaluation
        safeguards = self.safeguard_validator.evaluate(
            pt, journey, context, dist_nearest_valid, on_alt_route, now_dt
        )

        # 6. Score Calculator
        score = self.score_calculator.calculate_score(
            dist_nearest_valid, heading_diff_deg, pt, journey, context
        )

        # 7. Decision Tree Logic
        status = "NORMAL"
        primary_cause = "ON_TRACK_STANDARD_JOURNEY"
        explanation = ""

        if safeguards.approved_reroute_present:
            status = "NORMAL_REROUTED"
            primary_cause = "APPROVED_REROUTE_ACTIVE"
            explanation = f"Evidence-based classification: Shipment {journey.shipment_id} is operating under an approved reroute. Location is authorized."

        elif safeguards.signal_loss_only:
            status = "UNKNOWN_SIGNAL_MONITOR"
            primary_cause = "TELEMETRY_SIGNAL_LOSS"
            explanation = f"Evidence-based classification: Telemetry signal unavailable for shipment {journey.shipment_id}."

        elif (
            score >= self.config.misplaced_score_threshold
            and persistent_anomaly
            and dist_nearest_valid > self.config.max_off_route_distance_km
            and not safeguards.approved_reroute_present
            and not safeguards.vehicle_transfer_active
            and not safeguards.traffic_delay_only
            and not safeguards.signal_loss_only
        ):
            status = "MISPLACED"
            primary_cause = "PERSISTENT_UNAPPROVED_ROUTE_DEVIATION"
            explanation = (
                f"Evidence-based classification: Shipment {journey.shipment_id} is {dist_nearest_valid:.1f}km off all allowed routes "
                f"across {consecutive_off_count} consecutive observations (misplacement score: {score:.2f}). "
                f"No active vehicle transfer or approved reroute found."
            )

        elif safeguards.traffic_delay_only:
            status = "DELAYED"
            primary_cause = "ON_ROUTE_TRAFFIC_CONGESTION_DELAY"
            explanation = (
                f"Evidence-based classification: Shipment {journey.shipment_id} is delayed past target time, "
                f"but remains on valid corridor ({dist_nearest_valid:.1f}km deviation). Not misplaced."
            )

        elif (
            dist_nearest_valid > self.config.max_off_route_distance_km
            or consecutive_off_count >= 1
            or score >= 0.40
        ):
            status = "SUSPICIOUS"
            primary_cause = "UNCONFIRMED_LOCATION_DEVIATION"
            explanation = (
                f"Evidence-based classification: Location deviation detected for shipment {journey.shipment_id} ({dist_nearest_valid:.1f}km off route, "
                f"{consecutive_off_count} off-route observation(s), score: {score:.2f}). Insufficient observations for persistent misplacement."
            )

        else:
            status = "NORMAL"
            primary_cause = "ON_TRACK_STANDARD_JOURNEY"
            explanation = f"Evidence-based classification: Shipment {journey.shipment_id} is on-track along corridor ({dist_nearest_valid:.1f}km from primary route)."

        return DetectionResultDomain(
            alert_id=alert_id,
            shipment_id=journey.shipment_id,
            status=status,
            misplacement_score=score,
            location={"lat": pt.lat, "lng": pt.lng},
            assigned_vehicle=journey.vehicle_code,
            distance_to_primary_route_km=dist_primary,
            distance_to_nearest_valid_route_km=dist_nearest_valid,
            heading_difference_deg=round(heading_diff_deg, 1),
            persistent_anomaly=persistent_anomaly,
            safeguard_outcomes=safeguards,
            primary_cause=primary_cause,
            explanation=explanation,
            timestamp=now_dt,
        )
