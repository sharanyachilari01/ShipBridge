"""
Deterministic component scoring and multi-criteria ranking for piggyback recovery options.
"""

from typing import List
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG
from app.piggybacking_engine.models import ComponentScores, PiggybackOptionDomain


def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a numerical value within [min_val, max_val]."""
    return max(min_val, min(max_val, val))


class OptionScorer:
    def __init__(self, config: PiggybackConfig = DEFAULT_PIGGYBACK_CONFIG):
        self.config = config

    def calculate_scores(
        self,
        detour_distance_km: float,
        additional_time_hours: float,
        estimated_total_cost: float,
        available_weight_kg: float,
        remaining_weight_kg: float,
        available_volume_m3: float,
        remaining_volume_m3: float,
        deadline_margin_hours: float,
        route_overlap_km: float,
        num_transfers: int,
    ) -> ComponentScores:
        """
        Calculates individual component scores (0.0 to 1.0) and combined weighted score.
        """
        # Distance score: 1.0 - (detour / MAX_ACCEPTABLE_DETOUR_KM)
        s_distance = clamp(1.0 - (detour_distance_km / self.config.MAX_ACCEPTABLE_DETOUR_KM))

        # Time score: 1.0 - (extra_hours / MAX_ACCEPTABLE_EXTRA_TIME_HOURS)
        s_time = clamp(1.0 - (additional_time_hours / self.config.MAX_ACCEPTABLE_EXTRA_TIME_HOURS))

        # Cost score: 1.0 - (total_cost / MAX_ACCEPTABLE_RECOVERY_COST)
        s_cost = clamp(1.0 - (estimated_total_cost / self.config.MAX_ACCEPTABLE_RECOVERY_COST))

        # Capacity score: 0.5 * (rem_wt / avail_wt) + 0.5 * (rem_vol / avail_vol)
        wt_ratio = clamp(remaining_weight_kg / available_weight_kg) if available_weight_kg > 0 else 0.0
        vol_ratio = clamp(remaining_volume_m3 / available_volume_m3) if available_volume_m3 > 0 else 0.0
        s_capacity = clamp(0.5 * wt_ratio + 0.5 * vol_ratio)

        # Deadline score: clamp(deadline_margin_hrs / MAX_DEADLINE_MARGIN_HOURS)
        s_deadline = clamp(deadline_margin_hours / self.config.MAX_DEADLINE_MARGIN_HOURS)

        # Route score: clamp(overlap_km / MAX_ROUTE_OVERLAP_REFERENCE_KM)
        s_route = clamp(route_overlap_km / self.config.MAX_ROUTE_OVERLAP_REFERENCE_KM)

        # Transfer score: 1 / (1 + num_transfers)
        s_transfer = clamp(1.0 / (1.0 + float(num_transfers)))

        # Weighted combined score
        total_score = (
            self.config.WEIGHT_DISTANCE * s_distance
            + self.config.WEIGHT_TIME * s_time
            + self.config.WEIGHT_COST * s_cost
            + self.config.WEIGHT_DEADLINE * s_deadline
            + self.config.WEIGHT_CAPACITY * s_capacity
            + self.config.WEIGHT_ROUTE * s_route
            + self.config.WEIGHT_TRANSFER * s_transfer
        )

        return ComponentScores(
            distance_score=round(s_distance, 4),
            time_score=round(s_time, 4),
            cost_score=round(s_cost, 4),
            deadline_score=round(s_deadline, 4),
            capacity_score=round(s_capacity, 4),
            route_score=round(s_route, 4),
            transfer_score=round(s_transfer, 4),
            total_score=round(total_score, 4),
        )

    def rank_options(self, options: List[PiggybackOptionDomain]) -> List[PiggybackOptionDomain]:
        """
        Deterministically ranks options using multi-criteria sorting:
        1. piggyback_score descending
        2. estimated_delivery_time ascending
        3. estimated_total_cost ascending
        4. number_of_transfers ascending
        5. vehicle_id ascending
        """
        sorted_options = sorted(
            options,
            key=lambda x: (
                -x.piggyback_score,
                x.estimated_delivery_time,
                x.estimated_total_cost,
                x.number_of_transfers,
                x.vehicle_id,
            ),
        )

        for rank_idx, option in enumerate(sorted_options, start=1):
            option.rank = rank_idx

        return sorted_options
