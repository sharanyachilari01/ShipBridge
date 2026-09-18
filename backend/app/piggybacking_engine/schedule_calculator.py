"""
Schedule, timing, and deadline margin calculations.
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG


class ScheduleCalculator:
    def __init__(self, config: PiggybackConfig = DEFAULT_PIGGYBACK_CONFIG):
        self.config = config

    def calculate_schedule(
        self,
        current_time: datetime,
        detour_distance_km: float,
        route_overlap_km: float,
        pickup_deadline: Optional[datetime],
        delivery_deadline: Optional[datetime],
        num_transfers: int = 0,
    ) -> Tuple[datetime, datetime, float, float, str, Optional[str]]:
        """
        Calculate:
        - estimated_pickup_time
        - estimated_delivery_time
        - additional_time_hours
        - deadline_margin_hours
        - deadline_risk_level ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        - rejection_reason (if pickup window or deadline is missed)
        """
        # Calculate pickup travel time to pickup hub based on detour/distance
        pickup_travel_minutes = (detour_distance_km / self.config.AVERAGE_VEHICLE_SPEED_KMH) * 60.0
        
        # Pickup time is current_time + pickup travel time
        estimated_pickup = current_time + timedelta(minutes=max(10.0, pickup_travel_minutes))
        
        # Transport time for route leg(s)
        transport_minutes = (route_overlap_km / self.config.AVERAGE_VEHICLE_SPEED_KMH) * 60.0
        
        # Handling time for transfers
        handling_minutes = num_transfers * self.config.DEFAULT_HANDLING_TIME_MINUTES
        
        total_additional_minutes = pickup_travel_minutes + handling_minutes
        additional_time_hours = round(total_additional_minutes / 60.0, 2)
        
        total_transit_minutes = pickup_travel_minutes + transport_minutes + handling_minutes
        estimated_delivery = current_time + timedelta(minutes=total_transit_minutes)
        
        # Check pickup window feasibility
        rejection_reason = None
        if pickup_deadline and estimated_pickup > pickup_deadline:
            rejection_reason = "PICKUP_WINDOW_MISSED"
            
        # Calculate deadline margin
        if delivery_deadline:
            # Ensure datetime timezone compatibility
            if delivery_deadline.tzinfo and not estimated_delivery.tzinfo:
                estimated_delivery = estimated_delivery.replace(tzinfo=timezone.utc)
            elif not delivery_deadline.tzinfo and estimated_delivery.tzinfo:
                delivery_deadline = delivery_deadline.replace(tzinfo=timezone.utc)
                
            margin_seconds = (delivery_deadline - estimated_delivery).total_seconds()
            deadline_margin_hours = round(margin_seconds / 3600.0, 2)
            
            if deadline_margin_hours < 0:
                rejection_reason = "DEADLINE_MISSED"
                deadline_risk_level = "CRITICAL"
            elif deadline_margin_hours < 2.0:
                deadline_risk_level = "HIGH"
            elif deadline_margin_hours < 4.0:
                deadline_risk_level = "MEDIUM"
            else:
                deadline_risk_level = "LOW"
        else:
            deadline_margin_hours = 12.0
            deadline_risk_level = "LOW"
            
        return (
            estimated_pickup,
            estimated_delivery,
            additional_time_hours,
            deadline_margin_hours,
            deadline_risk_level,
            rejection_reason,
        )
