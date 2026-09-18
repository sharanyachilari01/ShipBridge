import math
from typing import List, Tuple, Optional
from app.detection.models_domain import TelemetryPoint, ExpectedJourney
from app.detection.config import DetectionConfig, DEFAULT_CONFIG
from app.detection.route_matcher import RouteMatcher, haversine_km


def calculate_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates compass heading angle (0-360 degrees) between two GPS points."""
    dlon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


def calculate_heading_difference(heading1: float, heading2: float) -> float:
    """Calculates minimal angular difference handling 0/360 wraparound."""
    diff = abs(heading1 - heading2) % 360.0
    return min(diff, 360.0 - diff)


class TrajectoryAnalyzer:
    """Analyzes trajectory history for persistent off-route anomalies and heading differences."""

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config
        self.route_matcher = RouteMatcher(config)

    def evaluate_persistence(
        self,
        recent_points: List[TelemetryPoint],
        journey: ExpectedJourney
    ) -> Tuple[bool, int]:
        """
        Evaluates whether recent telemetry points constitute a persistent route anomaly.
        Requires config.min_persistent_observations (default 3) consecutive off-route points (>15km).
        Returns:
            (persistent_anomaly_boolean, consecutive_off_route_count)
        """
        if not recent_points:
            return False, 0

        consecutive_off = 0
        for pt in reversed(recent_points):
            _, min_dist, _ = self.route_matcher.match_location(pt.lat, pt.lng, journey)
            if min_dist > self.config.max_off_route_distance_km:
                consecutive_off += 1
            else:
                break

        is_persistent = consecutive_off >= self.config.min_persistent_observations
        return is_persistent, consecutive_off

    def resolve_heading(
        self, current_point: TelemetryPoint, previous_point: Optional[TelemetryPoint]
    ) -> float:
        """Returns telemetry heading or derives heading from previous point if missing."""
        if current_point.heading_degrees is not None:
            return current_point.heading_degrees % 360.0

        if previous_point is not None:
            dist = haversine_km(previous_point.lat, previous_point.lng, current_point.lat, current_point.lng)
            if dist >= 0.05:  # Moving at least 50m
                return calculate_heading(previous_point.lat, previous_point.lng, current_point.lat, current_point.lng)

        return 0.0

    def compute_heading_difference(
        self,
        current_point: TelemetryPoint,
        previous_point: Optional[TelemetryPoint],
        expected_route_heading: float = 0.0
    ) -> float:
        """
        Computes heading difference in degrees.
        If speed <= low_speed_cutoff_kmh (20 km/h), returns 0.0 (ignored).
        """
        if current_point.speed_kmh <= self.config.low_speed_cutoff_kmh:
            return 0.0

        actual_heading = self.resolve_heading(current_point, previous_point)
        return calculate_heading_difference(actual_heading, expected_route_heading)
