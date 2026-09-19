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
  pickup_deadline?: string | null;
  delivery_deadline?: string | null;
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

// Stage 2 Types

export interface Stage2ComponentScores {
  distance_score: number;
  time_score: number;
  cost_score: number;
  deadline_score: number;
  capacity_score: number;
  route_score: number;
  transfer_score: number;
  total_score: number;
}

export interface Stage2LegDetail {
  leg_index: number;
  vehicle_id: number;
  vehicle_code: string;
  route_id: number;
  route_code: string;
  from_hub_id: number;
  from_hub_name: string;
  to_hub_id: number;
  to_hub_name: string;
  departure_time?: string;
  arrival_time?: string;
  distance_km: number;
}

export interface Stage2PiggybackOption {
  candidate_id: string;
  shipment_id: number;
  vehicle_id: number;
  vehicle_code: string;
  route_id: number;
  route_code: string;
  pickup_hub_id: number;
  pickup_hub_name: string;
  drop_hub_id: number;
  drop_hub_name: string;
  number_of_transfers: number;
  is_direct_piggyback: boolean;
  available_weight_capacity_kg: number;
  remaining_weight_capacity_kg: number;
  available_volume_capacity_m3: number;
  remaining_volume_capacity_m3: number;
  route_overlap_km: number;
  detour_distance_km: number;
  additional_time_hours: number;
  estimated_pickup_time: string;
  estimated_delivery_time: string;
  transport_cost: number;
  transfer_cost: number;
  estimated_total_cost: number;
  cost_savings_vs_dedicated: number;
  deadline_margin_hours: number;
  deadline_risk_level: string;
  transfer_complexity: string;
  is_feasible: boolean;
  rejection_reasons: string[];
  component_scores: Stage2ComponentScores;
  piggyback_score: number;
  rank: number;
  explanation: string;
  concerns: string[];
  legs: Stage2LegDetail[];
  route_geometry: Array<{ lat: number; lng: number }>;
}

export interface Stage2AnalysisResult {
  run_id: string;
  shipment_id: number;
  analyzed_at: string;
  misplaced_location?: { latitude: number; longitude: number } | null;
  eligible: boolean;
  ineligibility_reason?: string | null;
  total_candidates_evaluated: number;
  feasible_candidates_count: number;
  opportunities: Stage2PiggybackOption[];
  rejected_candidates: Array<Record<string, any>>;
}

export interface AtRiskAlert {
  alert_id: number;
  shipment_id: number;
  tracking_number?: string;
  risk_level: string;
  reasons: string[];
  current_deviation_km: number;
  deadline_buffer_minutes: number;
  created_timestamp: string;
  is_resolved: boolean;
}

export interface SimulationRequest {
  additional_route_delay_hours: number;
  additional_handling_delay_minutes: number;
  available_capacity_adjustment_percent: number;
  cost_multiplier: number;
  priority_override?: string;
  transfer_hub_unavailable?: string;
}

export interface RankChange {
  opportunity_id: number;
  vehicle_code: string;
  baseline_rank?: number | null;
  simulated_rank?: number | null;
  rank_delta: number;
  status_change: string;
}

export interface NewlyInfeasibleCandidate {
  opportunity_id: number;
  vehicle_code: string;
  route_code: string;
  rejection_reasons: string[];
}

export interface SimulationComparison {
  baseline_cost: number;
  simulated_cost: number;
  cost_delta: number;
  baseline_eta?: string | null;
  simulated_eta?: string | null;
  eta_delay_minutes: number;
  baseline_deadline_margin_minutes: number;
  simulated_deadline_margin_minutes: number;
  baseline_score: number;
  simulated_score: number;
  score_delta: number;
  recommendation_changed: boolean;
  change_summary: string;
}

export interface SimulationResult {
  shipment_id: number;
  tracking_number: string;
  simulation_inputs: {
    additional_route_delay_hours: number;
    additional_handling_delay_minutes: number;
    available_capacity_adjustment_percent: number;
    cost_multiplier: number;
    priority_override: string;
  };
  baseline_recommended_option?: any | null;
  simulated_recommended_option?: any | null;
  baseline_options: any[];
  simulated_options: any[];
  rank_changes: RankChange[];
  newly_infeasible_candidates: NewlyInfeasibleCandidate[];
  comparison: SimulationComparison;
  has_feasible_simulated_option: boolean;
}
