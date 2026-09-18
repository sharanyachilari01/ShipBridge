"""
Distance calculations using Haversine formula and spatial geometry metrics.
"""

import math
from typing import List, Dict, Any, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle distance between two points on Earth in kilometers."""
    R = 6371.0  # Earth radius in kilometers
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


def calculate_route_length_km(geometry: List[Dict[str, Any]]) -> float:
    """Calculate the total cumulative distance along a route geometry array."""
    if not geometry or len(geometry) < 2:
        return 0.0
    
    total_dist = 0.0
    for i in range(len(geometry) - 1):
        p1 = geometry[i]
        p2 = geometry[i + 1]
        lat1 = float(p1.get("lat", 0.0))
        lon1 = float(p1.get("lng", p1.get("lon", 0.0)))
        lat2 = float(p2.get("lat", 0.0))
        lon2 = float(p2.get("lng", p2.get("lon", 0.0)))
        total_dist += haversine_km(lat1, lon1, lat2, lon2)
    return total_dist


def find_closest_point_on_route(
    lat: float, lon: float, geometry: List[Dict[str, Any]]
) -> Tuple[float, Dict[str, float], int]:
    """
    Find the closest point on a route geometry array to a given lat/lon point.
    Returns (min_distance_km, closest_point_dict, segment_index).
    """
    if not geometry:
        return float("inf"), {"lat": lat, "lng": lon}, -1
    
    min_dist = float("inf")
    closest_pt = {"lat": lat, "lng": lon}
    closest_idx = 0
    
    for idx, pt in enumerate(geometry):
        pt_lat = float(pt.get("lat", 0.0))
        pt_lng = float(pt.get("lng", pt.get("lon", 0.0)))
        dist = haversine_km(lat, lon, pt_lat, pt_lng)
        if dist < min_dist:
            min_dist = dist
            closest_pt = {"lat": pt_lat, "lng": pt_lng}
            closest_idx = idx
            
    return min_dist, closest_pt, closest_idx


def calculate_detour_distance_km(
    shipment_lat: float,
    shipment_lng: float,
    pickup_hub_lat: float,
    pickup_hub_lng: float,
    drop_hub_lat: float,
    drop_hub_lng: float,
    original_route_km: float = 0.0,
) -> float:
    """
    Calculate the additional detour distance in km required for a vehicle to:
    1. Divert from current route/location to pickup hub (or shipment location if direct)
    2. Travel from pickup hub to drop hub
    3. Return to normal route/destination.
    
    For piggybacking:
    Detour = dist(shipment_loc, pickup_hub) + (extra deviation to drop_hub vs direct route).
    If pickup hub is on or near the vehicle's route, detour is primarily pickup_distance + dropoff_deviation.
    """
    pickup_dist = haversine_km(shipment_lat, shipment_lng, pickup_hub_lat, pickup_hub_lng)
    # Direct leg between hubs
    transfer_dist = haversine_km(pickup_hub_lat, pickup_hub_lng, drop_hub_lat, drop_hub_lng)
    
    # Detour estimate: pickup connection + minor adjustment (if route passes through hubs, detour is just pickup connection)
    detour = pickup_dist
    return round(detour, 2)


def calculate_route_overlap_km(
    pickup_hub_lat: float,
    pickup_hub_lng: float,
    drop_hub_lat: float,
    drop_hub_lng: float,
    route_geometry: List[Dict[str, Any]],
) -> float:
    """
    Calculate the portion of the vehicle's route (in km) that overlaps between the pickup and drop hubs.
    """
    if not route_geometry or len(route_geometry) < 2:
        # Fallback to direct distance between hubs
        return round(haversine_km(pickup_hub_lat, pickup_hub_lng, drop_hub_lat, drop_hub_lng), 2)
    
    _, _, p_idx = find_closest_point_on_route(pickup_hub_lat, pickup_hub_lng, route_geometry)
    _, _, d_idx = find_closest_point_on_route(drop_hub_lat, drop_hub_lng, route_geometry)
    
    if p_idx < 0 or d_idx < 0 or p_idx >= d_idx:
        # If pickup is after drop or invalid, fallback to direct hub distance
        return round(haversine_km(pickup_hub_lat, pickup_hub_lng, drop_hub_lat, drop_hub_lng), 2)
    
    sub_geometry = route_geometry[p_idx : d_idx + 1]
    return round(calculate_route_length_km(sub_geometry), 2)
