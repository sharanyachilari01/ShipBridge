"""
Hard feasibility evaluation and rejection tagging.
"""

from typing import List, Tuple
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG
from app.piggybacking_engine.models import CandidateVehicleDomain


class FeasibilityChecker:
    def __init__(self, config: PiggybackConfig = DEFAULT_PIGGYBACK_CONFIG):
        self.config = config

    def check_feasibility(
        self,
        vehicle: CandidateVehicleDomain,
        shipment_weight_kg: float,
        shipment_volume_m3: float,
        remaining_weight_capacity_kg: float,
        remaining_volume_capacity_m3: float,
        detour_distance_km: float,
        additional_time_hours: float,
        estimated_total_cost: float,
        deadline_margin_hours: float,
        num_transfers: int,
        initial_rejection_reasons: List[str] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Evaluates all hard operational and constraint bounds.
        Returns (is_feasible, list_of_rejection_reasons).
        """
        rejection_reasons = list(initial_rejection_reasons or [])

        # 1. Vehicle status
        if vehicle.status and vehicle.status.upper() in ["MAINTENANCE", "INACTIVE", "OUT_OF_SERVICE"]:
            if "VEHICLE_NOT_OPERATIONAL" not in rejection_reasons:
                rejection_reasons.append("VEHICLE_NOT_OPERATIONAL")

        # 2. Weight capacity
        if remaining_weight_capacity_kg < shipment_weight_kg:
            if "INSUFFICIENT_WEIGHT_CAPACITY" not in rejection_reasons:
                rejection_reasons.append("INSUFFICIENT_WEIGHT_CAPACITY")

        # 3. Volume capacity
        if remaining_volume_capacity_m3 < shipment_volume_m3:
            if "INSUFFICIENT_VOLUME_CAPACITY" not in rejection_reasons:
                rejection_reasons.append("INSUFFICIENT_VOLUME_CAPACITY")

        # 4. Detour threshold
        if detour_distance_km > self.config.MAX_ACCEPTABLE_DETOUR_KM:
            if "ROUTE_INCOMPATIBLE" not in rejection_reasons:
                rejection_reasons.append("ROUTE_INCOMPATIBLE")

        # 5. Extra time threshold
        if additional_time_hours > self.config.MAX_ACCEPTABLE_EXTRA_TIME_HOURS:
            if "DEADLINE_MISSED" not in rejection_reasons:
                rejection_reasons.append("DEADLINE_MISSED")

        # 6. Max hops/transfers threshold
        if num_transfers > self.config.MAX_HOPS - 1:
            if "TRANSFER_NOT_ALLOWED" not in rejection_reasons:
                rejection_reasons.append("TRANSFER_NOT_ALLOWED")

        # 7. Deadline margin threshold
        if deadline_margin_hours < 0:
            if "DEADLINE_MISSED" not in rejection_reasons:
                rejection_reasons.append("DEADLINE_MISSED")

        is_feasible = len(rejection_reasons) == 0
        return is_feasible, rejection_reasons
