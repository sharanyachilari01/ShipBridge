from typing import Optional, List, Any
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
    weight_kg: float = 100.0
    priority: str = "NORMAL"
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


