"""
Domain models and dataclasses for Stage 3 Recovery Selection & Impact Analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Stage3ImpactMetrics:
    baseline_recovery_cost: float
    selected_recovery_cost: float
    estimated_cost_savings: float
    baseline_delivery_time: Optional[datetime]
    selected_delivery_time: datetime
    delivery_time_change_minutes: int
    deadline_margin_minutes: int
    additional_distance_km: float
    additional_time_hours: float
    number_of_transfers: int
    transfer_complexity: str
    deadline_risk: str
    vehicle_available_weight_kg: float
    vehicle_available_volume_m3: float
    remaining_weight_capacity_kg: float
    remaining_volume_capacity_m3: float
    capacity_utilization_after_percent: float
    is_high_capacity_utilization: bool
    impact_summary: str


@dataclass
class Stage3ComponentScores:
    piggyback_score_norm: float = 0.0
    cost_savings_score: float = 0.0
    deadline_buffer_score: float = 0.0
    capacity_impact_score: float = 0.0
    transfer_simplicity_score: float = 0.0
    delivery_time_score: float = 0.0
    selection_score: float = 0.0


@dataclass
class EvaluatedOptionDomain:
    opportunity_id: int
    shipment_id: int
    vehicle_id: int
    vehicle_code: str
    route_id: Optional[int]
    route_code: str
    pickup_hub_id: Optional[int]
    pickup_hub_name: str
    drop_hub_id: Optional[int]
    drop_hub_name: str
    is_direct_piggyback: bool
    number_of_transfers: int
    estimated_total_cost: float
    estimated_delivery_time: datetime
    deadline_margin_minutes: int
    stage2_piggyback_score: float
    remaining_weight_capacity_kg: float = 5000.0
    remaining_volume_capacity_m3: float = 20.0
    component_scores: Stage3ComponentScores = field(default_factory=Stage3ComponentScores)
    selection_score: float = 0.0
    rank: int = 0
    designation: str = "ALTERNATIVE"  # "RECOMMENDED" or "ALTERNATIVE"
    impact_metrics: Optional[Stage3ImpactMetrics] = None
    explanation: str = ""
    concerns: List[str] = field(default_factory=list)
    route_geometry: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RecommendationResultDomain:
    recommendation_id: str
    analysis_id: Optional[str]
    shipment_id: int
    tracking_number: str
    shipment_priority: str
    shipment_status: str
    recommendation_status: str  # PENDING_REVIEW, APPROVED, REJECTED, SUPERSEDED, NO_FEASIBLE_RECOVERY_OPTIONS
    recommendation_score: float = 0.0
    recommendation_reason: str = ""
    recommended_option: Optional[EvaluatedOptionDomain] = None
    alternative_options: List[EvaluatedOptionDomain] = field(default_factory=list)
    created_at: Optional[datetime] = None
    decisions: List[Dict[str, Any]] = field(default_factory=list)
