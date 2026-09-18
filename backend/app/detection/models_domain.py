from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Waypoint:
    hub_id: Optional[int]
    hub_name: str
    lat: float
    lng: float
    sequence: int = 1


@dataclass
class RouteGeometry:
    route_code: str
    waypoints: List[Waypoint]


@dataclass
class ExpectedJourney:
    shipment_id: str
    origin_hub_id: int
    origin_code: str
    destination_hub_id: int
    destination_code: str
    expected_next_hub_id: Optional[int]
    primary_route: RouteGeometry
    allowed_alternative_routes: List[RouteGeometry] = field(default_factory=list)
    assigned_vehicle_id: Optional[int] = None
    vehicle_code: str = "UNASSIGNED"
    expected_arrival_time: Optional[datetime] = None
    delivery_deadline: Optional[datetime] = None


@dataclass
class TelemetryPoint:
    lat: float
    lng: float
    timestamp: datetime
    speed_kmh: float = 0.0
    heading_degrees: Optional[float] = None
    gps_accuracy_meters: float = 10.0
    ble_gateway_id: Optional[str] = None
    tracking_available: bool = True


@dataclass
class SystemContext:
    approved_reroute_active: bool = False
    active_vehicle_transfer: bool = False
    transfer_started_at: Optional[datetime] = None
    transfer_gateway_id: Optional[str] = None
    traffic_delay_active: bool = False


@dataclass
class SafeguardOutcomes:
    approved_reroute_present: bool = False
    vehicle_transfer_active: bool = False
    traffic_delay_only: bool = False
    signal_loss_only: bool = False
    gps_accuracy_valid: bool = True
    on_allowed_alternative_route: bool = False
    low_speed_heading_ignored: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return {
            "approved_reroute_present": self.approved_reroute_present,
            "vehicle_transfer_active": self.vehicle_transfer_active,
            "traffic_delay_only": self.traffic_delay_only,
            "signal_loss_only": self.signal_loss_only,
            "gps_accuracy_valid": self.gps_accuracy_valid,
            "on_allowed_alternative_route": self.on_allowed_alternative_route,
            "low_speed_heading_ignored": self.low_speed_heading_ignored,
        }


@dataclass
class DetectionResultDomain:
    alert_id: str
    shipment_id: str
    status: str  # NORMAL, DELAYED, NORMAL_REROUTED, UNKNOWN_SIGNAL_MONITOR, SUSPICIOUS, MISPLACED
    misplacement_score: float
    location: Dict[str, float]
    assigned_vehicle: str
    distance_to_primary_route_km: float
    distance_to_nearest_valid_route_km: float
    heading_difference_deg: float
    persistent_anomaly: bool
    safeguard_outcomes: SafeguardOutcomes
    primary_cause: str
    explanation: str
    timestamp: datetime
