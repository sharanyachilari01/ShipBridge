"""
Impact Calculator for Stage 3 Recovery Selection.
Calculates cost, delivery-time, resource, and operational impact metrics.
"""

from datetime import datetime, timezone
from typing import Optional
from app.recovery_selection.config import Stage3Config, DEFAULT_STAGE3_CONFIG
from app.recovery_selection.models import Stage3ImpactMetrics


class ImpactCalculator:
    def __init__(self, config: Stage3Config = DEFAULT_STAGE3_CONFIG):
        self.config = config

    def calculate_impact(
        self,
        shipment_weight_kg: float,
        shipment_volume_m3: float,
        delivery_deadline: Optional[datetime],
        estimated_total_cost: float,
        estimated_delivery_time: datetime,
        deadline_margin_minutes: int,
        detour_distance_km: float,
        additional_time_hours: float,
        number_of_transfers: int,
        transfer_complexity: str,
        deadline_risk: str,
        available_weight_kg: float,
        remaining_weight_kg: float,
        available_volume_m3: float,
        remaining_volume_m3: float,
    ) -> Stage3ImpactMetrics:
        """
        Calculates Stage 3 impact metrics for a single piggyback recovery opportunity.
        """
        baseline_cost = self.config.DEDICATED_RECOVERY_BASE_COST
        selected_cost = round(estimated_total_cost, 2)
        cost_savings = max(0.0, round(baseline_cost - selected_cost, 2))

        baseline_delivery = delivery_deadline

        if baseline_delivery and estimated_delivery_time:
            # Time zone handling
            if baseline_delivery.tzinfo and not estimated_delivery_time.tzinfo:
                estimated_delivery_time = estimated_delivery_time.replace(tzinfo=timezone.utc)
            elif not baseline_delivery.tzinfo and estimated_delivery_time.tzinfo:
                baseline_delivery = baseline_delivery.replace(tzinfo=timezone.utc)
                
            time_diff_sec = (baseline_delivery - estimated_delivery_time).total_seconds()
            delivery_time_change_min = int(time_diff_sec / 60.0)
        else:
            delivery_time_change_min = 0

        # Capacity utilization after adding shipment
        used_wt = max(0.0, available_weight_kg - remaining_weight_kg)
        wt_util_pct = (used_wt / available_weight_kg * 100.0) if available_weight_kg > 0 else 50.0

        used_vol = max(0.0, available_volume_m3 - remaining_volume_m3)
        vol_util_pct = (used_vol / available_volume_m3 * 100.0) if available_volume_m3 > 0 else 50.0

        capacity_utilization_pct = round(max(wt_util_pct, vol_util_pct), 1)
        is_high_util = capacity_utilization_pct >= self.config.HIGH_CAPACITY_UTILIZATION_PERCENT

        margin_hrs = round(deadline_margin_minutes / 60.0, 1)
        transfers_desc = "no transfers" if number_of_transfers == 0 else f"{number_of_transfers} transfer(s)"
        
        impact_summary = (
            f"Estimated cost: ₹{selected_cost:.2f} (Savings: ₹{cost_savings:.2f} vs ₹{baseline_cost:.0f} baseline). "
            f"Delivery deadline margin: {margin_hrs} hrs ({deadline_risk} risk). "
            f"Transfers: {transfers_desc}. Post-load capacity utilization: {capacity_utilization_pct}%."
        )

        return Stage3ImpactMetrics(
            baseline_recovery_cost=baseline_cost,
            selected_recovery_cost=selected_cost,
            estimated_cost_savings=cost_savings,
            baseline_delivery_time=baseline_delivery,
            selected_delivery_time=estimated_delivery_time,
            delivery_time_change_minutes=delivery_time_change_min,
            deadline_margin_minutes=deadline_margin_minutes,
            additional_distance_km=round(detour_distance_km, 1),
            additional_time_hours=round(additional_time_hours, 1),
            number_of_transfers=number_of_transfers,
            transfer_complexity=transfer_complexity or "DIRECT",
            deadline_risk=deadline_risk or "LOW",
            vehicle_available_weight_kg=round(available_weight_kg, 1),
            vehicle_available_volume_m3=round(available_volume_m3, 1),
            remaining_weight_capacity_kg=round(remaining_weight_kg, 1),
            remaining_volume_capacity_m3=round(remaining_volume_m3, 1),
            capacity_utilization_after_percent=capacity_utilization_pct,
            is_high_capacity_utilization=is_high_util,
            impact_summary=impact_summary,
        )
