"""
Cost calculation and cost savings estimation.
"""

from typing import Tuple
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG


class CostCalculator:
    def __init__(self, config: PiggybackConfig = DEFAULT_PIGGYBACK_CONFIG):
        self.config = config

    def calculate_cost(
        self,
        detour_distance_km: float,
        additional_time_hours: float,
        num_transfers: int,
        direct_shipment_distance_km: float = 50.0,
    ) -> Tuple[float, float, float, float]:
        """
        Calculates:
        - transport_cost
        - transfer_cost
        - estimated_total_cost
        - cost_savings_vs_dedicated
        """
        additional_time_minutes = additional_time_hours * 60.0
        
        transport_cost = (detour_distance_km * self.config.COST_PER_KM) + (
            additional_time_minutes * self.config.COST_PER_MINUTE
        )
        transport_cost = round(max(20.0, transport_cost), 2)
        
        transfer_cost = round(num_transfers * self.config.BASE_TRANSFER_FEE, 2)
        
        estimated_total_cost = round(transport_cost + transfer_cost, 2)
        
        # Dedicated recovery vehicle cost baseline (Base fee 300 + 25/km)
        dedicated_recovery_cost = max(350.0, direct_shipment_distance_km * 25.0 + 200.0)
        
        cost_savings = max(0.0, round(dedicated_recovery_cost - estimated_total_cost, 2))
        
        return transport_cost, transfer_cost, estimated_total_cost, cost_savings
