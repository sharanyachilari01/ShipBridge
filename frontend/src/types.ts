export interface Hub {
  id: number;
  code: string;
  name: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  hub_type: string;
}

export type ShipmentStatus = 'ON_TRACK' | 'MISPLACED' | 'RECOVERING' | 'DELIVERED' | 'DELAYED';
export type PriorityLevel = 'NORMAL' | 'HIGH' | 'CRITICAL';

export interface Shipment {
  id: number;
  shipment_id?: string;
  tracking_number: string;
  origin_hub_id: number;
  destination_hub_id: number;
  expected_next_hub_id?: number | null;
  assigned_vehicle_id?: number | null;
  current_hub_id?: number | null;
  current_lat?: number | null;
  current_lng?: number | null;
  status: ShipmentStatus;
  weight_kg: number;
  volume_m3?: number;
  priority: PriorityLevel;
  misplaced_at?: string | null;
  notes?: string | null;
  created_at: string;
  origin_hub?: Hub | null;
  destination_hub?: Hub | null;
  expected_next_hub?: Hub | null;
  current_hub?: Hub | null;
}

export interface Waypoint {
  hub_id: number;
  hub_name: string;
  lat: number;
  lng: number;
  eta: string;
  sequence: number;
}

export interface VehicleRoute {
  id: number;
  vehicle_code: string;
  vehicle_type: string;
  driver_name: string;
  max_capacity_kg: number;
  spare_capacity_kg: number;
  waypoints: Waypoint[];
  status: string;
}

export interface PiggybackRecommendation {
  recommendation_id: string;
  shipment: Shipment;
  vehicle_route: VehicleRoute;
  pickup_hub: Hub;
  dropoff_hub: Hub;
  match_score: number;
  cost_saved: number;
  co2_saved_kg: number;
  explanation: string;
  spare_capacity_after_kg: number;
}

export interface RecoveryPlanRequest {
  shipment_id: number;
  vehicle_route_id: number;
  pickup_hub_id: number;
  dropoff_hub_id: number;
  cost_saved: number;
  co2_saved_kg: number;
  explanation: string;
}

export interface ImpactMetrics {
  total_cost_saved: number;
  total_co2_saved_kg: number;
  total_recoveries_count: number;
  piggyback_success_rate: number;
  active_misplaced_count: number;
  monthly_comparison: Array<{
    month: string;
    dedicated_cost: number;
    piggyback_cost: number;
    savings: number;
  }>;
  co2_trend: Array<{
    month: string;
    co2_saved_kg: number;
  }>;
  recovery_method_distribution: Array<{
    name: string;
    value: number;
  }>;
}

export interface BackendHealth {
  status: 'ok' | 'degraded' | 'offline';
  db?: string;
  hubs_loaded?: number;
  message?: string;
}

export interface SafeguardOutcomes {
  approved_reroute_present: boolean;
  vehicle_transfer_active: boolean;
  traffic_delay_only: boolean;
  signal_loss_only: boolean;
  gps_accuracy_valid: boolean;
  on_allowed_alternative_route: boolean;
  low_speed_heading_ignored: boolean;
}

export interface DemoShipmentAnalysis {
  id: number;
  shipment_id: string;
  tracking_number: string;
  origin_hub: string;
  destination_hub: string;
  expected_next_hub: string;
  assigned_vehicle: string;
  current_status: string;
  misplacement_score: number;
  distance_to_primary_route_km: number;
  distance_to_nearest_valid_route_km: number;
  heading_difference_deg: number;
  persistent_anomaly: boolean;
  safeguard_outcomes: SafeguardOutcomes;
  primary_cause: string;
  explanation: string;
  current_lat: number;
  current_lng: number;
  speed_kmh: number;
  telemetry_points_count: number;
}

export interface FinalEvaluation {
  id: number;
  evaluation_id: number;
  shipment_id: number;
  tracking_number?: string;
  original_cost: number;
  recovery_cost: number;
  cost_saved: number;
  total_savings: number;
  co2_offset: number;
  time_saved_hours: number;
  deadline_met: boolean;
  recovery_success_status: string;
  additional_distance_km: number;
}

export interface ShipmentException {
  id: number;
  exception_id: number;
  shipment_id: number;
  tracking_number?: string;
  exception_type: string;
  severity: string;
  detected_timestamp: string;
  confidence_score: number;
  exception_details?: string;
  is_synthetic: boolean;
}


