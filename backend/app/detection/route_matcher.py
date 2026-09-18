import math
from typing import Tuple, List
from app.detection.models_domain import ExpectedJourney, RouteGeometry, Waypoint
from app.detection.config import DetectionConfig, DEFAULT_CONFIG


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Haversine distance in kilometres using Earth radius R = 6371 km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def point_to_segment_distance_km(
    plat: float, plng: float, lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Computes minimum distance from point (plat, plng) to line segment (lat1, lon1)-(lat2, lon2) in km."""
    # Projection parameter t on segment
    dx = lon2 - lon1
    dy = lat2 - lat1
    if dx == 0 and dy == 0:
        return haversine_km(plat, plng, lat1, lon1)

    t = ((plng - lon1) * dx + (plat - lat1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    proj_lat = lat1 + t * dy
    proj_lng = lon1 + t * dx
    return haversine_km(plat, plng, proj_lat, proj_lng)


def route_distance_km(lat: float, lng: float, route: RouteGeometry) -> float:
    """Calculates minimum distance in km from telemetry point to any segment in route geometry."""
    if not route.waypoints:
        return 999.0

    if len(route.waypoints) == 1:
        wp = route.waypoints[0]
        return haversine_km(lat, lng, wp.lat, wp.lng)

    min_dist = float("inf")
    for i in range(len(route.waypoints) - 1):
        wp1 = route.waypoints[i]
        wp2 = route.waypoints[i + 1]
        dist = point_to_segment_distance_km(lat, lng, wp1.lat, wp1.lng, wp2.lat, wp2.lng)
        if dist < min_dist:
            min_dist = dist

    return min_dist


class RouteMatcher:
    """Matches telemetry location against primary and allowed alternative routes using Haversine distance."""

    def __init__(self, config: DetectionConfig = DEFAULT_CONFIG):
        self.config = config

    def match_location(
        self, lat: float, lng: float, journey: ExpectedJourney
    ) -> Tuple[float, float, bool]:
        """
        Returns:
            (distance_to_primary_route_km, distance_to_nearest_valid_route_km, is_on_allowed_alternative_route)
        """
        dist_primary = route_distance_km(lat, lng, journey.primary_route)

        all_valid_routes = [journey.primary_route] + journey.allowed_alternative_routes
        min_valid_dist = dist_primary
        on_alt_route = False

        for alt_route in journey.allowed_alternative_routes:
            alt_dist = route_distance_km(lat, lng, alt_route)
            if alt_dist < min_valid_dist:
                min_valid_dist = alt_dist

            if alt_dist <= self.config.max_off_route_distance_km and dist_primary > self.config.max_off_route_distance_km:
                on_alt_route = True

        return (
            round(dist_primary, 2),
            round(min_valid_dist, 2),
            on_alt_route,
        )
