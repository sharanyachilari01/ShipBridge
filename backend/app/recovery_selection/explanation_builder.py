"""
Explanation and Concerns Builder for Stage 3 Recovery Selection.
Generates deterministic, template-driven human-readable rationale without LLM dependency.
"""

from typing import List, Tuple
from app.recovery_selection.config import Stage3Config, DEFAULT_STAGE3_CONFIG
from app.recovery_selection.models import EvaluatedOptionDomain


class ExplanationBuilder:
    def __init__(self, config: Stage3Config = DEFAULT_STAGE3_CONFIG):
        self.config = config

    def build_explanation_and_concerns(
        self, option: EvaluatedOptionDomain
    ) -> Tuple[str, List[str]]:
        """
        Builds a deterministic explanation string and list of operational concerns.
        """
        metrics = option.impact_metrics
        concerns = []

        if not metrics:
            return "Feasible recovery option based on Stage 2 matching.", []

        # High capacity utilization concern
        if metrics.is_high_capacity_utilization:
            concerns.append(
                f"Capacity utilization reaches {metrics.capacity_utilization_after_percent}%, "
                f"which is above the configured monitoring threshold of {self.config.HIGH_CAPACITY_UTILIZATION_PERCENT:.0f}%."
            )

        # Deadline margin concern
        margin_hours = metrics.deadline_margin_minutes / 60.0
        if metrics.deadline_margin_minutes < self.config.TIGHT_DEADLINE_MARGIN_MINUTES:
            concerns.append(
                f"Tight deadline buffer ({margin_hours:.1f} hours remaining before delivery deadline)."
            )

        # Transfer count concern
        if metrics.number_of_transfers >= self.config.HIGH_TRANSFER_COUNT:
            concerns.append(
                f"Requires {metrics.number_of_transfers} hub transfers, introducing operational handling risk."
            )

        # Detour distance concern
        if metrics.additional_distance_km > 20.0:
            concerns.append(
                f"Requires detour of {metrics.additional_distance_km:.1f} km from primary route."
            )

        # Build natural language explanation
        if option.designation == "RECOMMENDED":
            rank_desc = "Recommended because it has the highest feasible selection score"
        else:
            rank_desc = f"Ranked #{option.rank} alternative option"

        transfer_desc = (
            "requires no additional transfer"
            if metrics.number_of_transfers == 0
            else f"requires {metrics.number_of_transfers} transfer(s)"
        )

        preserved_cap_pct = max(0.0, round(100.0 - metrics.capacity_utilization_after_percent, 1))

        explanation = (
            f"{rank_desc} ({option.selection_score:.2f}), "
            f"arrives {margin_hours:.1f} hours before the deadline, "
            f"{transfer_desc}, preserves {preserved_cap_pct}% vehicle capacity, "
            f"and saves an estimated ₹{metrics.estimated_cost_savings:.2f} "
            f"compared with the configured dedicated-recovery baseline (₹{metrics.baseline_recovery_cost:.0f})."
        )

        return explanation, concerns
