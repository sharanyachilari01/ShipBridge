"""
Domain models and dataclasses for Stage 2 Piggybacking & Recovery Opportunity Engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class Location:
    latitude: float
    longitude: float

@dataclass
class CandidateVehicleDomain:
    vehicle_id: int
    vehicle_code: str
    status: str  # "EN_ROUTE", "IDLE", "IN_TRANSIT", "MAINTENANCE"
    weight_capacity_kg: float
    volume_capacity_m3: float
    assigned_hub_id: Optional[int] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    current_route_id: Optional[int] = None

@dataclass
class CandidateHubDomain:
    hub_id: int
    code: str
    name: str
    city: str
    state: str
    latitude: float
    longitude: float
    active: bool = True

@dataclass
class CandidateRouteDomain:
    route_id: int
    route_code: str
    origin_hub_id: int
    destination_hub_id: int
    route_geometry: List[Dict[str, Any]]
    active: bool = True

@dataclass
class LegDetail:
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

@dataclass
class ComponentScores:
    distance_score: float = 0.0
    time_score: float = 0.0
    cost_score: float = 0.0
    deadline_score: float = 0.0
    capacity_score: float = 0.0
    route_score: float = 0.0
    transfer_score: float = 0.0
    total_score: float = 0.0

@dataclass
class PiggybackOptionDomain:
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
    deadline_risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    transfer_complexity: str  # "DIRECT", "SINGLE_TRANSFER", "MULTI_TRANSFER"
    
    is_feasible: bool
    rejection_reasons: List[str] = field(default_factory=list)
    
    component_scores: ComponentScores = field(default_factory=ComponentScores)
    piggyback_score: float = 0.0
    rank: int = 0
    
    explanation: str = ""
    concerns: List[str] = field(default_factory=list)
    legs: List[LegDetail] = field(default_factory=list)
    route_geometry: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AnalysisResultDomain:
    run_id: str
    shipment_id: int
    analyzed_at: datetime
    misplaced_location: Optional[Dict[str, float]]
    eligible: bool
    ineligibility_reason: Optional[str]
    total_candidates_evaluated: int
    feasible_candidates_count: int
    opportunities: List[PiggybackOptionDomain] = field(default_factory=list)
    rejected_candidates: List[Dict[str, Any]] = field(default_factory=list)
