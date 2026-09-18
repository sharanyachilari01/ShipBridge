from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class HubBase(BaseModel):
    code: str
    name: str
    city: str
    state: str
    latitude: float
    longitude: float
    active: bool = True
    is_synthetic: bool = True


class HubResponse(HubBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class VehicleBase(BaseModel):
    vehicle_code: str
    type: str
    capacity_kg: float
    assigned_hub_id: Optional[int] = None
    status: str = "ACTIVE"
    is_synthetic: bool = True


class VehicleResponse(VehicleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ShipmentCreate(BaseModel):
    shipment_id: Optional[str] = None
    tracking_number: str
    origin_hub_id: int
    destination_hub_id: int
    expected_next_hub_id: Optional[int] = None
    current_hub_id: Optional[int] = None
    assigned_vehicle_id: Optional[int] = None
    weight_kg: float = 100.0
    volume_m3: float = 1.0
    priority: str = "NORMAL"
    pickup_deadline: Optional[datetime] = None
    delivery_deadline: Optional[datetime] = None
    notes: Optional[str] = None
    simulate_misplaced: Optional[bool] = False


class ShipmentResponse(BaseModel):
    id: int
    shipment_id: str
    tracking_number: str
    origin_hub_id: int
    destination_hub_id: int
    expected_next_hub_id: Optional[int] = None
    assigned_vehicle_id: Optional[int] = None
    priority: str
    status: str
    weight_kg: float
    delivery_deadline: Optional[datetime] = None
    expected_arrival_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_synthetic: bool

    origin_hub: Optional[HubResponse] = None
    destination_hub: Optional[HubResponse] = None
    expected_next_hub: Optional[HubResponse] = None
    assigned_vehicle: Optional[VehicleResponse] = None

    current_lat: Optional[float] = None
    current_lng: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class VehicleRouteResponse(BaseModel):
    id: int
    vehicle_code: str
    vehicle_type: str
    driver_name: str
    max_capacity_kg: float
    spare_capacity_kg: float
    waypoints: List[Any]
    status: str

    model_config = ConfigDict(from_attributes=True)


class PiggybackRecommendation(BaseModel):
    recommendation_id: str
    shipment: ShipmentResponse
    vehicle_route: VehicleRouteResponse
    pickup_hub: HubResponse
    dropoff_hub: HubResponse
    match_score: int
    cost_saved: float
    co2_saved_kg: float
    explanation: str
    spare_capacity_after_kg: float


class AcceptRecoveryRequest(BaseModel):
    shipment_id: int
    vehicle_route_id: int
    pickup_hub_id: int
    dropoff_hub_id: int
    cost_saved: float
    co2_saved_kg: float
    explanation: str


class RecoveryPlanResponse(BaseModel):
    id: int
    shipment_id: int
    assigned_vehicle_id: int
    pickup_hub_id: int
    dropoff_hub_id: int
    cost_saved: float
    co2_saved_kg: float
    approved_at: datetime
    explanation: str
    is_synthetic: bool

    model_config = ConfigDict(from_attributes=True)


class ImpactMetrics(BaseModel):
    total_cost_saved: float
    total_co2_saved_kg: float
    total_recoveries_count: int
    piggyback_success_rate: float
    active_misplaced_count: int
    monthly_comparison: List[dict]
    co2_trend: List[dict]
    recovery_method_distribution: List[dict]


class SafeguardOutcomesSchema(BaseModel):
    approved_reroute_present: bool
    vehicle_transfer_active: bool
    traffic_delay_only: bool
    signal_loss_only: bool
    gps_accuracy_valid: bool
    on_allowed_alternative_route: bool
    low_speed_heading_ignored: bool


class DetectionCheckRequest(BaseModel):
    shipment_id: Any


class DetectionCheckResponse(BaseModel):
    alert_id: str
    shipment_id: str
    status: str
    misplacement_score: float
    location: dict
    assigned_vehicle: str
    distance_to_primary_route_km: float
    distance_to_nearest_valid_route_km: float
    heading_difference_deg: float
    persistent_anomaly: bool
    safeguard_outcomes: SafeguardOutcomesSchema
    primary_cause: str
    explanation: str
    timestamp: datetime


class DemoShipmentAnalysis(BaseModel):
    id: int
    shipment_id: str
    tracking_number: str
    origin_hub: str
    destination_hub: str
    expected_next_hub: str
    assigned_vehicle: str
    current_status: str
    misplacement_score: float
    distance_to_primary_route_km: float
    distance_to_nearest_valid_route_km: float
    heading_difference_deg: float
    persistent_anomaly: bool
    safeguard_outcomes: dict
    primary_cause: str
    explanation: str
    current_lat: float
    current_lng: float
    speed_kmh: float
    telemetry_points_count: int


class FinalEvaluationResponse(BaseModel):
    id: int
    evaluation_id: int
    shipment_id: int
    tracking_number: Optional[str] = None
    original_cost: float
    recovery_cost: float
    cost_saved: float
    total_savings: float
    co2_offset: float
    time_saved_hours: float
    deadline_met: bool
    recovery_success_status: str
    additional_distance_km: float

    model_config = ConfigDict(from_attributes=True)


class ShipmentExceptionResponse(BaseModel):
    id: int
    exception_id: int
    shipment_id: int
    tracking_number: Optional[str] = None
    exception_type: str
    severity: str
    detected_timestamp: datetime
    confidence_score: float
    exception_details: Optional[str] = None
    is_synthetic: bool

    model_config = ConfigDict(from_attributes=True)


# Stage 2 Piggybacking Engine Schemas

class Stage2ComponentScoresSchema(BaseModel):
    distance_score: float
    time_score: float
    cost_score: float
    deadline_score: float
    capacity_score: float
    route_score: float
    transfer_score: float
    total_score: float


class Stage2LegDetailSchema(BaseModel):
    leg_index: int
    vehicle_id: int
    vehicle_code: str
    route_id: int
    route_code: str
    from_hub_id: int
    from_hub_name: str
    to_hub_id: int
    to_hub_name: str
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    distance_km: float = 0.0


class Stage2PiggybackOptionResponse(BaseModel):
    candidate_id: str
    shipment_id: int
    vehicle_id: int
    vehicle_code: str
    route_id: int
    route_code: str
    pickup_hub_id: int
    pickup_hub_name: str
    drop_hub_id: int
    drop_hub_name: str
    number_of_transfers: int
    is_direct_piggyback: bool
    available_weight_capacity_kg: float
    remaining_weight_capacity_kg: float
    available_volume_capacity_m3: float
    remaining_volume_capacity_m3: float
    route_overlap_km: float
    detour_distance_km: float
    additional_time_hours: float
    estimated_pickup_time: datetime
    estimated_delivery_time: datetime
    transport_cost: float
    transfer_cost: float
    estimated_total_cost: float
    cost_savings_vs_dedicated: float
    deadline_margin_hours: float
    deadline_risk_level: str
    transfer_complexity: str
    is_feasible: bool
    rejection_reasons: List[str]
    component_scores: Stage2ComponentScoresSchema
    piggyback_score: float
    rank: int
    explanation: str
    concerns: List[str]
    legs: List[Stage2LegDetailSchema]
    route_geometry: List[Dict[str, Any]]


class Stage2AnalysisResponse(BaseModel):
    run_id: str
    shipment_id: int
    analyzed_at: datetime
    misplaced_location: Optional[Dict[str, float]] = None
    eligible: bool
    ineligibility_reason: Optional[str] = None
    total_candidates_evaluated: int
    feasible_candidates_count: int
    opportunities: List[Stage2PiggybackOptionResponse]
    rejected_candidates: List[Dict[str, Any]]


# Stage 3 Recovery Selection & Impact Analysis Schemas

class Stage3ImpactMetricsSchema(BaseModel):
    baseline_recovery_cost: float
    selected_recovery_cost: float
    estimated_cost_savings: float
    baseline_delivery_time: Optional[datetime] = None
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


class Stage3ScoresSchema(BaseModel):
    piggyback_score_norm: float
    cost_savings_score: float
    deadline_buffer_score: float
    capacity_impact_score: float
    transfer_simplicity_score: float
    delivery_time_score: float
    selection_score: float


class EvaluatedOptionResponse(BaseModel):
    opportunity_id: int
    shipment_id: int
    vehicle_id: int
    vehicle_code: str
    route_id: Optional[int] = None
    route_code: str
    pickup_hub_id: Optional[int] = None
    pickup_hub_name: str
    drop_hub_id: Optional[int] = None
    drop_hub_name: str
    is_direct_piggyback: bool
    number_of_transfers: int
    estimated_total_cost: float
    estimated_delivery_time: datetime
    deadline_margin_minutes: int
    stage2_piggyback_score: float
    component_scores: Stage3ScoresSchema
    selection_score: float
    rank: int
    designation: str
    impact_metrics: Optional[Stage3ImpactMetricsSchema] = None
    explanation: str
    concerns: List[str]
    route_geometry: List[Dict[str, Any]]


class RecommendationResultResponse(BaseModel):
    recommendation_id: str
    analysis_id: Optional[str] = None
    shipment_id: int
    tracking_number: str
    shipment_priority: str
    shipment_status: str
    recommendation_status: str
    recommendation_score: float
    recommendation_reason: str
    recommended_option: Optional[EvaluatedOptionResponse] = None
    alternative_options: List[EvaluatedOptionResponse]
    created_at: Optional[datetime] = None
    decisions: List[Dict[str, Any]]


class ApproveRecommendationRequest(BaseModel):
    dispatcher_name: str
    decision_note: Optional[str] = None


class RejectRecommendationRequest(BaseModel):
    dispatcher_name: str
    decision_note: str


class Stage3DashboardResponse(BaseModel):
    total_misplaced_shipments: int
    shipments_with_feasible_options: int
    pending_reviews_count: int
    approved_recommendations_count: int
    rejected_recommendations_count: int
    total_estimated_cost_savings: float
    average_deadline_margin_minutes: float
    average_deadline_margin_hours: float
    approval_rate_percent: float
    recovery_options_by_type: List[Dict[str, Any]]
    cost_comparison: List[Dict[str, Any]]
    high_priority_unresolved_count: int
    manager_briefing: Dict[str, Any]
    is_synthetic_estimate: bool = True


# What-If Simulation Schemas

class SimulationRequest(BaseModel):
    additional_route_delay_hours: float = 0.0
    additional_handling_delay_minutes: float = 0.0
    available_capacity_adjustment_percent: float = 0.0
    cost_multiplier: float = 1.0
    priority_override: Optional[str] = None


class RankChangeSchema(BaseModel):
    opportunity_id: int
    vehicle_code: str
    baseline_rank: Optional[int] = None
    simulated_rank: Optional[int] = None
    rank_delta: int = 0
    status_change: str = "UNCHANGED"


class NewlyInfeasibleCandidateSchema(BaseModel):
    opportunity_id: int
    vehicle_code: str
    route_code: str
    rejection_reasons: List[str]


class SimulationComparisonMetricsSchema(BaseModel):
    baseline_cost: float
    simulated_cost: float
    cost_delta: float
    baseline_eta: Optional[datetime] = None
    simulated_eta: Optional[datetime] = None
    eta_delay_minutes: float
    baseline_deadline_margin_minutes: int
    simulated_deadline_margin_minutes: int
    baseline_score: float
    simulated_score: float
    score_delta: float
    recommendation_changed: bool
    change_summary: str


class SimulationResponse(BaseModel):
    shipment_id: int
    tracking_number: str
    simulation_inputs: Dict[str, Any]
    baseline_recommended_option: Optional[EvaluatedOptionResponse] = None
    simulated_recommended_option: Optional[EvaluatedOptionResponse] = None
    baseline_options: List[EvaluatedOptionResponse]
    simulated_options: List[EvaluatedOptionResponse]
    rank_changes: List[RankChangeSchema]
    newly_infeasible_candidates: List[NewlyInfeasibleCandidateSchema]
    comparison: SimulationComparisonMetricsSchema
    has_feasible_simulated_option: bool

