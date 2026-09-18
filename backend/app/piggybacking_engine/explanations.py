"""
Deterministic, template-driven explanation generator for piggyback recovery options.
"""

from typing import List, Tuple
from app.piggybacking_engine.models import PiggybackOptionDomain


def generate_explanation_and_concerns(
    option: PiggybackOptionDomain,
) -> Tuple[str, List[str]]:
    """
    Generate an explainable summary text and list of potential concerns.
    """
    concerns = []

    if option.detour_distance_km > 20.0:
        concerns.append(f"Significant detour required ({option.detour_distance_km:.1f} km).")

    if option.additional_time_hours > 1.5:
        concerns.append(f"High additional delay ({option.additional_time_hours:.1f} hrs).")

    if option.deadline_risk_level in ["HIGH", "CRITICAL"]:
        concerns.append(f"Tight delivery deadline margin ({option.deadline_margin_hours:.1f} hrs remaining).")

    if option.number_of_transfers > 0:
        concerns.append(f"Requires {option.number_of_transfers} hub transfer(s), introducing handling complexity.")

    if option.remaining_weight_capacity_kg < 500.0:
        concerns.append(f"Limited remaining vehicle weight capacity ({option.remaining_weight_capacity_kg:.1f} kg).")

    # Generate explanation sentence
    if option.is_direct_piggyback:
        route_desc = f"Direct piggyback via Vehicle {option.vehicle_code} on Route {option.route_code}"
    else:
        route_desc = f"Multi-hop transfer route via Vehicle {option.vehicle_code} with {option.number_of_transfers} transfer(s)"

    pickup_desc = f"Pickup at {option.pickup_hub_name} and dropoff at {option.drop_hub_name}."
    metrics_desc = (
        f"Detour: {option.detour_distance_km:.1f} km, Extra Time: {option.additional_time_hours:.1f} hrs, "
        f"Est. Cost: ${option.estimated_total_cost:.2f} (Savings: ${option.cost_savings_vs_dedicated:.2f})."
    )

    explanation = f"{route_desc}. {pickup_desc} {metrics_desc}"

    return explanation, concerns
