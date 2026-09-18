"""
Discovery of candidate vehicles, active routes, and pickup/drop/transfer hubs.
"""

from typing import List, Tuple, Optional, Dict
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG
from app.piggybacking_engine.models import (
    CandidateVehicleDomain,
    CandidateHubDomain,
    CandidateRouteDomain,
    Location,
)
from app.piggybacking_engine.distance_calculator import haversine_km


class CandidateFinder:
    def __init__(self, config: PiggybackConfig = DEFAULT_PIGGYBACK_CONFIG):
        self.config = config

    def find_candidate_vehicles(
        self, vehicles: List[CandidateVehicleDomain]
    ) -> Tuple[List[CandidateVehicleDomain], List[Dict]]:
        """
        Filter operational candidate vehicles.
        Rejects vehicles in MAINTENANCE status or without valid operational info.
        """
        valid_candidates = []
        rejected = []
        
        for v in vehicles:
            status_upper = (v.status or "").upper()
            if status_upper in ["MAINTENANCE", "INACTIVE", "OUT_OF_SERVICE"]:
                rejected.append({
                    "vehicle_id": v.vehicle_id,
                    "vehicle_code": v.vehicle_code,
                    "rejection_reason": "VEHICLE_NOT_OPERATIONAL"
                })
            else:
                valid_candidates.append(v)
                
        return valid_candidates, rejected

    def find_pickup_hubs(
        self,
        shipment_location: Location,
        all_hubs: List[CandidateHubDomain],
        origin_hub_id: Optional[int] = None,
    ) -> List[Tuple[CandidateHubDomain, float]]:
        """
        Find active hubs within MAX_PICKUP_HUB_DISTANCE_KM of the misplaced shipment location.
        If no hub is within range, includes the shipment's origin hub or the nearest hub as fallback.
        Returns list of (Hub, distance_km).
        """
        eligible_pickup_hubs = []
        nearest_hub = None
        nearest_dist = float("inf")
        
        for hub in all_hubs:
            if not hub.active:
                continue
            dist = haversine_km(
                shipment_location.latitude,
                shipment_location.longitude,
                hub.latitude,
                hub.longitude,
            )
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_hub = hub
                
            if dist <= self.config.MAX_PICKUP_HUB_DISTANCE_KM:
                eligible_pickup_hubs.append((hub, round(dist, 2)))
                
        # Fallback to origin hub or nearest hub if none within 20km threshold
        if not eligible_pickup_hubs and nearest_hub:
            eligible_pickup_hubs.append((nearest_hub, round(nearest_dist, 2)))
            
        # Sort by distance
        eligible_pickup_hubs.sort(key=lambda x: x[1])
        return eligible_pickup_hubs

    def find_drop_hubs(
        self,
        destination_hub_id: int,
        all_hubs: List[CandidateHubDomain],
        destination_location: Optional[Location] = None,
    ) -> List[Tuple[CandidateHubDomain, float]]:
        """
        Find active drop hubs near the shipment's intended destination.
        Always includes the target destination hub itself (distance 0.0).
        Includes alternative hubs within MAX_DROP_HUB_DISTANCE_KM.
        Returns list of (Hub, distance_km).
        """
        target_hub = next((h for h in all_hubs if h.hub_id == destination_hub_id and h.active), None)
        eligible_drop_hubs = []
        
        if target_hub:
            eligible_drop_hubs.append((target_hub, 0.0))
            
        ref_lat = target_hub.latitude if target_hub else (destination_location.latitude if destination_location else None)
        ref_lng = target_hub.longitude if target_hub else (destination_location.longitude if destination_location else None)
        
        if ref_lat is not None and ref_lng is not None:
            for hub in all_hubs:
                if not hub.active or hub.hub_id == destination_hub_id:
                    continue
                dist = haversine_km(ref_lat, ref_lng, hub.latitude, hub.longitude)
                if dist <= self.config.MAX_DROP_HUB_DISTANCE_KM:
                    eligible_drop_hubs.append((hub, round(dist, 2)))
                    
        eligible_drop_hubs.sort(key=lambda x: x[1])
        return eligible_drop_hubs
