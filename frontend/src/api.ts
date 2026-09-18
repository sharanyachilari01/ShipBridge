import {
  BackendHealth,
  Hub,
  Shipment,
  VehicleRoute,
  PiggybackRecommendation,
  RecoveryPlanRequest,
  ImpactMetrics,
  FinalEvaluation,
  ShipmentException
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<BackendHealth> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      return { status: 'offline' };
    }
    return await res.json();
  } catch (err) {
    return { status: 'offline' };
  }
}

export async function fetchHubs(): Promise<Hub[]> {
  const res = await fetch(`${API_BASE}/hubs`);
  if (!res.ok) throw new Error('Failed to fetch hubs');
  return res.json();
}

export async function fetchShipments(status?: string): Promise<Shipment[]> {
  const url = status ? `${API_BASE}/shipments?status=${encodeURIComponent(status)}` : `${API_BASE}/shipments`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch shipments');
  return res.json();
}

export async function createShipment(payload: {
  tracking_number: string;
  origin_hub_id: number;
  destination_hub_id: number;
  current_hub_id?: number;
  weight_kg: number;
  volume_m3: number;
  priority: string;
  notes?: string;
  simulate_misplaced?: boolean;
}): Promise<Shipment> {
  const res = await fetch(`${API_BASE}/shipments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create shipment');
  return res.json();
}

export async function markShipmentMisplaced(shipmentId: number, notes?: string): Promise<Shipment> {
  const url = notes
    ? `${API_BASE}/shipments/${shipmentId}/mark-misplaced?notes=${encodeURIComponent(notes)}`
    : `${API_BASE}/shipments/${shipmentId}/mark-misplaced`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to mark shipment misplaced');
  return res.json();
}

export async function fetchRoutes(): Promise<VehicleRoute[]> {
  const res = await fetch(`${API_BASE}/routes`);
  if (!res.ok) throw new Error('Failed to fetch vehicle routes');
  return res.json();
}

export async function fetchPiggybackRecommendations(shipmentId?: number): Promise<PiggybackRecommendation[]> {
  const url = shipmentId
    ? `${API_BASE}/recovery/recommendations?shipment_id=${shipmentId}`
    : `${API_BASE}/recovery/recommendations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch recommendations');
  return res.json();
}

export async function acceptRecoveryPlan(payload: RecoveryPlanRequest) {
  const res = await fetch(`${API_BASE}/recovery/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to accept recovery plan');
  return res.json();
}

export async function fetchImpactMetrics(): Promise<ImpactMetrics> {
  const res = await fetch(`${API_BASE}/impact`);
  if (!res.ok) throw new Error('Failed to fetch impact metrics');
  return res.json();
}

export async function triggerSeedData() {
  const res = await fetch(`${API_BASE}/seed`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to seed database');
  return res.json();
}

export async function fetchDemoShipmentsAnalysis() {
  const res = await fetch('/api/v1/demo/shipments');
  if (!res.ok) throw new Error('Failed to fetch demo shipments analysis');
  return res.json();
}

export async function fetchEvaluations(): Promise<FinalEvaluation[]> {
  const res = await fetch('/api/v1/evaluations');
  if (!res.ok) throw new Error('Failed to fetch evaluations');
  return res.json();
}

export async function fetchExceptions(): Promise<ShipmentException[]> {
  const res = await fetch('/api/v1/exceptions');
  if (!res.ok) throw new Error('Failed to fetch exceptions');
  return res.json();
}


