"""
Selection Engine for Stage 3 Recovery Selection.
Calculates Stage 3 Selection Score and performs deterministic ranking.
"""

from typing import List, Tuple
from app.recovery_selection.config import Stage3Config, DEFAULT_STAGE3_CONFIG
from app.recovery_selection.models import (
    EvaluatedOptionDomain,
    Stage3ComponentScores,
)
from app.recovery_selection.impact_calculator import ImpactCalculator
from app.recovery_selection.explanation_builder import ExplanationBuilder


def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a numerical value within [min_val, max_val]."""
    return max(min_val, min(max_val, val))


class SelectionEngine:
    def __init__(self, config: Stage3Config = DEFAULT_STAGE3_CONFIG):
        self.config = config
        self.impact_calculator = ImpactCalculator(config)
        self.explanation_builder = ExplanationBuilder(config)

    def evaluate_and_rank_options(
        self,
        shipment_weight_kg: float,
        shipment_volume_m3: float,
        shipment_priority: str,
        raw_options: List[EvaluatedOptionDomain],
    ) -> List[EvaluatedOptionDomain]:
        """
        Evaluates impact, computes component scores, calculates Stage 3 Selection Score,
        and ranks candidates deterministically.
        """
        evaluated: List[EvaluatedOptionDomain] = []

        for opt in raw_options:
            # Enforce feasibility rules: candidate must be deadline-feasible and capacity-feasible
            if opt.deadline_margin_minutes < 0:
                continue
            if opt.remaining_weight_capacity_kg < shipment_weight_kg or opt.remaining_volume_capacity_m3 < shipment_volume_m3:
                continue

            # Calculate impact metrics
            impact = self.impact_calculator.calculate_impact(
                shipment_weight_kg=shipment_weight_kg,
                shipment_volume_m3=shipment_volume_m3,
                delivery_deadline=opt.estimated_delivery_time,
                estimated_total_cost=opt.estimated_total_cost,
                estimated_delivery_time=opt.estimated_delivery_time,
                deadline_margin_minutes=opt.deadline_margin_minutes,
                detour_distance_km=opt.impact_metrics.additional_distance_km if opt.impact_metrics else 0.0,
                additional_time_hours=opt.impact_metrics.additional_time_hours if opt.impact_metrics else 0.0,
                number_of_transfers=opt.number_of_transfers,
                transfer_complexity=opt.impact_metrics.transfer_complexity if opt.impact_metrics else "DIRECT",
                deadline_risk=opt.impact_metrics.deadline_risk if opt.impact_metrics else "LOW",
                available_weight_kg=opt.impact_metrics.vehicle_available_weight_kg if opt.impact_metrics else 10000.0,
                remaining_weight_kg=opt.remaining_weight_capacity_kg,
                available_volume_m3=opt.impact_metrics.vehicle_available_volume_m3 if opt.impact_metrics else 40.0,
                remaining_volume_m3=opt.remaining_volume_capacity_m3,
            )
            opt.impact_metrics = impact

            # Calculate Stage 3 component scores (0.0 to 1.0)
            norm_piggyback = clamp(opt.stage2_piggyback_score)
            cost_savings_score = clamp(impact.estimated_cost_savings / self.config.DEDICATED_RECOVERY_BASE_COST)
            deadline_buffer_score = clamp(impact.deadline_margin_minutes / (6.0 * 60.0))
            capacity_impact_score = clamp(1.0 - (impact.capacity_utilization_after_percent / 100.0))
            transfer_simplicity_score = clamp(1.0 / (1.0 + float(opt.number_of_transfers)))
            delivery_time_score = clamp(1.0 - (impact.additional_time_hours / 4.0))

            # Combine weighted Selection Score
            selection_score = (
                self.config.WEIGHT_PIGGYBACK_SCORE * norm_piggyback
                + self.config.WEIGHT_COST_SAVINGS * cost_savings_score
                + self.config.WEIGHT_DEADLINE_BUFFER * deadline_buffer_score
                + self.config.WEIGHT_CAPACITY_IMPACT * capacity_impact_score
                + self.config.WEIGHT_TRANSFER_SIMPLICITY * transfer_simplicity_score
                + self.config.WEIGHT_DELIVERY_TIME * delivery_time_score
            )

            opt.component_scores = Stage3ComponentScores(
                piggyback_score_norm=round(norm_piggyback, 4),
                cost_savings_score=round(cost_savings_score, 4),
                deadline_buffer_score=round(deadline_buffer_score, 4),
                capacity_impact_score=round(capacity_impact_score, 4),
                transfer_simplicity_score=round(transfer_simplicity_score, 4),
                delivery_time_score=round(delivery_time_score, 4),
                selection_score=round(selection_score, 4),
            )
            opt.selection_score = round(selection_score, 4)

            evaluated.append(opt)

        if not evaluated:
            return []

        # Deterministic multi-criteria ranking:
        # 1. selection_score descending
        # 2. deadline_margin_minutes descending
        # 3. estimated_total_cost ascending
        # 4. number_of_transfers ascending
        # 5. vehicle_id ascending
        ranked = sorted(
            evaluated,
            key=lambda x: (
                -x.selection_score,
                -x.deadline_margin_minutes,
                x.estimated_total_cost,
                x.number_of_transfers,
                x.vehicle_id,
            ),
        )

        for idx, item in enumerate(ranked, start=1):
            item.rank = idx
            item.designation = "RECOMMENDED" if idx == 1 else "ALTERNATIVE"
            explanation, concerns = self.explanation_builder.build_explanation_and_concerns(item)
            item.explanation = explanation
            item.concerns = concerns

        return ranked
