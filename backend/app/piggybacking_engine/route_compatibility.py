"""
Route compatibility matching for direct and multi-hop piggybacking opportunities.
"""

from typing import List, Dict, Any, Optional, Tuple
from app.piggybacking_engine.models import (
    CandidateVehicleDomain,
    CandidateRouteDomain,
    CandidateHubDomain,
    LegDetail,
)
from app.piggybacking_engine.distance_calculator import find_closest_point_on_route


class RouteCompatibilityMatcher:
    """
    Evaluates whether a candidate vehicle's route is compatible with moving a shipment
    from a pickup hub to a drop hub directly or via hub transfer.
    """

    def check_direct_route_compatibility(
        self,
        vehicle: CandidateVehicleDomain,
        route: CandidateRouteDomain,
        pickup_hub: CandidateHubDomain,
        drop_hub: CandidateHubDomain,
    ) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        Check if a single vehicle on a given route can transport from pickup_hub to drop_hub.
        Returns (is_compatible, rejection_reason, route_geometry_slice).
        """
        if not route.active:
            return False, "ROUTE_NOT_ACTIVE", []

        geometry = route.route_geometry or []
        
        # Check if route connects origin to destination or passes through both hubs in sequence
        direct_match = (
            route.origin_hub_id == pickup_hub.hub_id
            and route.destination_hub_id == drop_hub.hub_id
        )
        
        if direct_match:
            return True, None, geometry
            
        # If geometry is present, check sequential indices of pickup and drop hubs along the route
        if len(geometry) >= 2:
            _, _, p_idx = find_closest_point_on_route(
                pickup_hub.latitude, pickup_hub.longitude, geometry
            )
            _, _, d_idx = find_closest_point_on_route(
                drop_hub.latitude, drop_hub.longitude, geometry
            )
            
            if p_idx >= 0 and d_idx >= 0 and p_idx < d_idx:
                return True, None, geometry[p_idx : d_idx + 1]
                
        # Also match if pickup_hub is origin OR drop_hub is destination and sequence is plausible
        if route.origin_hub_id == pickup_hub.hub_id or route.destination_hub_id == drop_hub.hub_id:
            return True, None, geometry

        return False, "ROUTE_INCOMPATIBLE", []

    def find_two_hop_route_compatibility(
        self,
        vehicle1: CandidateVehicleDomain,
        route1: CandidateRouteDomain,
        vehicle2: CandidateVehicleDomain,
        route2: CandidateRouteDomain,
        pickup_hub: CandidateHubDomain,
        drop_hub: CandidateHubDomain,
        all_hubs: List[CandidateHubDomain],
    ) -> Tuple[bool, Optional[CandidateHubDomain], Optional[str]]:
        """
        Check if vehicle1 (on route1) and vehicle2 (on route2) can form a 2-hop piggyback route
        via a shared transfer hub.
        """
        if not route1.active or not route2.active:
            return False, None, "ROUTE_NOT_ACTIVE"

        # Transfer hub candidate is route1's destination if it equals route2's origin
        if route1.destination_hub_id == route2.origin_hub_id:
            transfer_hub_id = route1.destination_hub_id
            transfer_hub = next((h for h in all_hubs if h.hub_id == transfer_hub_id and h.active), None)
            
            if not transfer_hub:
                return False, None, "HUB_UNAVAILABLE"
                
            # Check route1 connects pickup to transfer, and route2 connects transfer to drop
            leg1_ok, _, _ = self.check_direct_route_compatibility(vehicle1, route1, pickup_hub, transfer_hub)
            leg2_ok, _, _ = self.check_direct_route_compatibility(vehicle2, route2, transfer_hub, drop_hub)
            
            if leg1_ok and leg2_ok:
                return True, transfer_hub, None

        return False, None, "ROUTE_INCOMPATIBLE"
