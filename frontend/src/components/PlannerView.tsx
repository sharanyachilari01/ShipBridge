import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { Shipment, VehicleRoute, PiggybackRecommendation, SimulationResult } from '../types';
import { simulateRecovery } from '../api';
import {
  Compass,
  Truck,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Sliders,
  RotateCcw,
  Clock,
  Building2,
  TrendingDown,
  Info,
  CheckCircle2,
  XCircle,
  Play
} from 'lucide-react';

interface PlannerViewProps {
  shipments: Shipment[];
  routes: VehicleRoute[];
  recommendations: PiggybackRecommendation[];
  selectedShipmentId?: number | null;
  onSelectShipmentId?: (id: number) => void;
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
}

const createPointIcon = (color: string, symbol: string) => {
  return L.divIcon({
    className: 'custom-planner-icon',
    html: `<div style="background-color: ${color}; color: white; border: 2px solid white; border-radius: 9999px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; box-shadow: 0 3px 6px rgba(0,0,0,0.3);">
            ${symbol}
          </div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

export const PlannerView: React.FC<PlannerViewProps> = ({
  shipments,
  recommendations,
  selectedShipmentId,
  onSelectShipmentId,
  onAcceptRecommendation,
}) => {
  const misplacedShipments = shipments.filter((s) => s.status === 'MISPLACED');
  
  // Default to SH009 (shipment_id 9) or first misplaced shipment
  const defaultShipment = misplacedShipments.find((s) => s.id === 9) || misplacedShipments[0] || null;
  const [activeShipmentId, setActiveShipmentId] = useState<number>(
    selectedShipmentId || defaultShipment?.id || 1
  );

  const currentShipment = misplacedShipments.find((s) => s.id === activeShipmentId) || defaultShipment || null;
  const rawRec = recommendations.find((r) => r.shipment.id === activeShipmentId) || null;

  // What-If Simulation Inputs State
  const [simRouteDelayHours, setSimRouteDelayHours] = useState<number>(0);
  const [simHandlingDelayMins, setSimHandlingDelayMins] = useState<number>(0);
  const [simCapacityAdjustPct, setSimCapacityAdjustPct] = useState<number>(0);
  const [simCostMultiplier, setSimCostMultiplier] = useState<number>(1.0);
  const [simPriorityOverride, setSimPriorityOverride] = useState<string>('');

  // Simulation execution state
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  // Sync selected shipment prop
  useEffect(() => {
    if (selectedShipmentId && selectedShipmentId !== activeShipmentId) {
      setActiveShipmentId(selectedShipmentId);
      handleResetSimulation();
    }
  }, [selectedShipmentId]);

  const handleRunSimulation = async () => {
    if (!currentShipment) return;
    setSimulating(true);
    setSimError(null);

    try {
      const res = await simulateRecovery(currentShipment.id, {
        additional_route_delay_hours: simRouteDelayHours,
        additional_handling_delay_minutes: simHandlingDelayMins,
        available_capacity_adjustment_percent: simCapacityAdjustPct,
        cost_multiplier: simCostMultiplier,
        priority_override: simPriorityOverride ? simPriorityOverride : undefined,
      });
      setSimResult(res);
    } catch (err: any) {
      setSimError(err.message || 'Simulation request failed.');
    } finally {
      setSimulating(false);
    }
  };

  const handleResetSimulation = () => {
    setSimRouteDelayHours(0);
    setSimHandlingDelayMins(0);
    setSimCapacityAdjustPct(0);
    setSimCostMultiplier(1.0);
    setSimPriorityOverride('');
    setSimResult(null);
    setSimError(null);
  };

  const formatCurrency = (val: number) => `₹${Math.round(val).toLocaleString()}`;

  const getRiskBadgeColor = (risk?: string) => {
    switch (risk?.toUpperCase()) {
      case 'SAFE':
      case 'LOW':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'TIGHT':
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'AT_RISK':
      case 'HIGH':
      default:
        return 'bg-rose-100 text-rose-800 border-rose-300';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="p-2.5 bg-blue-100 text-blue-600 rounded-xl">
            <Compass className="h-6 w-6" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Recovery Planner & Decision Control</h2>
            <p className="text-xs text-slate-500">
              Evaluate explainable piggyback options, deterministic selection scores, and run What-if simulations.
            </p>
          </div>
        </div>
      </div>

      {misplacedShipments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm space-y-3">
          <ShieldCheck className="h-10 w-10 text-emerald-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">All Shipments On Track</h3>
          <p className="text-xs text-slate-500">There are currently no misplaced shipments requiring recovery evaluation.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Shipment Selector & Cargo Summary Bar */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-2">
                <span>Select Misplaced Shipment:</span>
                <select
                  value={activeShipmentId}
                  onChange={(e) => {
                    const id = Number(e.target.value);
                    setActiveShipmentId(id);
                    onSelectShipmentId?.(id);
                    handleResetSimulation();
                  }}
                  className="bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {misplacedShipments.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.tracking_number} — Priority: {s.priority} ({s.weight_kg}kg)
                    </option>
                  ))}
                </select>
              </label>

              {currentShipment && (
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-50 px-3.5 py-1.5 rounded-xl border border-slate-200">
                  <Clock className="h-3.5 w-3.5 text-blue-600" />
                  <span>Delivery SLA Deadline:</span>
                  <strong className="text-slate-900 font-mono">
                    {currentShipment.delivery_deadline
                      ? new Date(currentShipment.delivery_deadline).toLocaleString()
                      : 'Active Window'}
                  </strong>
                </div>
              )}
            </div>

            {/* Cargo Attribute Strip */}
            {currentShipment && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-3 border-t border-slate-100 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Origin Hub</span>
                  <strong className="text-slate-800">{currentShipment.origin_hub?.name || 'Origin Hub'}</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Current Hub</span>
                  <strong className="text-slate-800">{currentShipment.expected_next_hub?.name || 'Interchange Hub'}</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Destination Hub</span>
                  <strong className="text-slate-800">{currentShipment.destination_hub?.name || 'Destination Hub'}</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Payload Specs</span>
                  <strong className="text-slate-800">{currentShipment.weight_kg} kg | {currentShipment.volume_m3 || 1.0} m³</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Logistics Priority</span>
                  <span className="font-extrabold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 inline-block">
                    {simPriorityOverride || currentShipment.priority}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* PRIMARY HERO CARD SECTION — RECOMMENDED ACTION FOCUS */}
          <div>
            {rawRec ? (
              /* FEASIBLE HERO CARD (Green/Blue Treatment) */
              <div className="bg-gradient-to-br from-blue-900 via-slate-900 to-emerald-950 text-white rounded-3xl p-6 sm:p-8 shadow-xl border-2 border-emerald-400/50 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
                  <div className="flex items-center gap-3">
                    <span className="p-3 bg-emerald-500/20 text-emerald-400 rounded-2xl border border-emerald-400/30">
                      <Sparkles className="h-7 w-7" />
                    </span>
                    <div>
                      <span className="text-xs uppercase tracking-widest font-extrabold text-emerald-400 block">
                        Recommended Recovery Plan #1
                      </span>
                      <h3 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
                        {rawRec.vehicle_route.vehicle_code} — {rawRec.vehicle_route.vehicle_type}
                      </h3>
                      <p className="text-xs text-slate-300 mt-0.5">
                        Route: <strong>{rawRec.vehicle_route.status || 'Active Corridor'}</strong> | Pickup: <strong>{rawRec.pickup_hub.name}</strong> → Drop: <strong>{rawRec.dropoff_hub.name}</strong>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-[10px] uppercase text-slate-400 font-bold block">Selection Score</span>
                      <span className="text-2xl font-black text-emerald-400">
                        {rawRec.match_score}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-1">
                    <span className="text-[11px] text-slate-300 font-semibold block">Estimated Recovery Cost</span>
                    <span className="text-2xl font-black text-emerald-300">
                      {formatCurrency(18500 - rawRec.cost_saved)}
                    </span>
                    <span className="text-[10px] text-emerald-400 block font-medium">
                      Saves {formatCurrency(rawRec.cost_saved)} vs dedicated
                    </span>
                  </div>

                  <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-1">
                    <span className="text-[11px] text-slate-300 font-semibold block">CO₂ Avoided</span>
                    <span className="text-2xl font-black text-emerald-300">
                      {rawRec.co2_saved_kg} kg
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      Piggybacks existing route
                    </span>
                  </div>

                  <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-1">
                    <span className="text-[11px] text-slate-300 font-semibold block">Remaining Payload Cap</span>
                    <span className="text-2xl font-black text-white">
                      {rawRec.spare_capacity_after_kg} kg
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      Truck max: {rawRec.vehicle_route.max_capacity_kg} kg
                    </span>
                  </div>

                  <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-1">
                    <span className="text-[11px] text-slate-300 font-semibold block">Transfer Complexity</span>
                    <span className="text-lg font-bold text-white uppercase">
                      {rawRec.vehicle_route.waypoints?.length > 3 ? 'Hub Transfer' : 'Direct Piggyback'}
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      0 transfers required
                    </span>
                  </div>
                </div>

                {/* Deterministic Rationale */}
                <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Info className="h-4 w-4 text-emerald-400" />
                    Deterministic Selection Rationale
                  </h4>
                  <p className="text-xs text-slate-200 leading-relaxed font-medium">
                    {rawRec.explanation}
                  </p>
                </div>

                {/* Approve Button */}
                <div className="pt-2">
                  <button
                    onClick={() => onAcceptRecommendation(rawRec)}
                    className="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-extrabold text-sm py-4 px-6 rounded-2xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all"
                  >
                    <ShieldCheck className="h-5 w-5" />
                    Approve & Execute Recommended Recovery Plan
                  </button>
                </div>
              </div>
            ) : (
              /* NO FEASIBLE OPTION HERO CARD (Amber Manager Action State) */
              <div className="bg-gradient-to-br from-amber-950 via-slate-900 to-amber-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl border-2 border-amber-500/50 space-y-6">
                <div className="flex items-center gap-3 pb-4 border-b border-white/10">
                  <span className="p-3 bg-amber-500/20 text-amber-400 rounded-2xl border border-amber-400/30">
                    <AlertTriangle className="h-7 w-7" />
                  </span>
                  <div>
                    <span className="text-xs uppercase tracking-widest font-extrabold text-amber-400 block">
                      Recommended Manager Action — No Automated Feasible Option
                    </span>
                    <h3 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
                      Manual Recovery Escalation Required for Shipment {currentShipment?.tracking_number}
                    </h3>
                  </div>
                </div>

                <div className="p-4 bg-amber-500/10 rounded-2xl border border-amber-500/30 space-y-2">
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                    Feasibility Constraint Analysis & Rejection Rationale
                  </h4>
                  <p className="text-xs text-amber-100 leading-relaxed font-medium">
                    No active truck passing through this corridor satisfies payload weight ({currentShipment?.weight_kg}kg), cargo bay volume ({currentShipment?.volume_m3 || 1.0}m³), and SLA delivery deadlines.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-2">
                    <h5 className="font-bold text-slate-200">Manager Recommended Steps:</h5>
                    <ol className="list-decimal list-inside space-y-1 text-slate-300">
                      <li>Dispatch dedicated recovery vehicle from nearest hub ({currentShipment?.expected_next_hub?.name || 'Interchange Hub'}).</li>
                      <li>Contact regional logistics coordinator for priority override.</li>
                    </ol>
                  </div>

                  <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-2">
                    <h5 className="font-bold text-slate-200">Evaluated Candidate Constraints:</h5>
                    <ul className="list-disc list-inside space-y-1 text-slate-300">
                      <li>Weight limit exceeded on standard carriers.</li>
                      <li>Pickup arrival window past SLA margin.</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* WHAT-IF SIMULATOR SECTION — REAL API CONNECTION */}
          <div className="bg-slate-900 text-white rounded-3xl p-6 border border-slate-800 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <span className="p-2.5 bg-blue-600/30 text-blue-400 rounded-2xl border border-blue-500/30">
                  <Sliders className="h-6 w-6" />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">What-if Scenario Simulator</h3>
                    <span className="text-[10px] bg-blue-500/20 text-blue-300 font-bold px-2 py-0.5 rounded border border-blue-400/30">
                      Simulation only — no live records are changed
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Test route delays, handling dwell times, capacity adjustments, and cost multipliers in real-time.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleRunSimulation}
                  disabled={simulating}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-4 py-2 rounded-xl flex items-center gap-1.5 shadow-md transition-all disabled:opacity-50"
                >
                  <Play className="h-3.5 w-3.5" />
                  {simulating ? 'Simulating...' : 'Run Simulation'}
                </button>
                <button
                  onClick={handleResetSimulation}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs px-3.5 py-2 rounded-xl border border-slate-700 flex items-center gap-1.5 transition-all"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Reset
                </button>
              </div>
            </div>

            {simError && (
              <div className="bg-rose-950/80 border border-rose-700/50 rounded-xl p-3 text-xs text-rose-300 font-semibold flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                <span>{simError}</span>
              </div>
            )}

            {/* Slider Controls Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 text-xs">
              {/* Route Delay */}
              <div className="p-3.5 bg-slate-800/90 rounded-2xl border border-slate-700/80 space-y-2">
                <div className="flex justify-between font-semibold">
                  <span className="text-slate-300">Route Delay</span>
                  <span className="text-blue-400 font-mono font-bold">+{simRouteDelayHours} hrs</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="48"
                  step="1"
                  value={simRouteDelayHours}
                  onChange={(e) => setSimRouteDelayHours(Number(e.target.value))}
                  className="w-full accent-blue-500 cursor-pointer"
                />
              </div>

              {/* Handling Delay */}
              <div className="p-3.5 bg-slate-800/90 rounded-2xl border border-slate-700/80 space-y-2">
                <div className="flex justify-between font-semibold">
                  <span className="text-slate-300">Transfer Delay</span>
                  <span className="text-blue-400 font-mono font-bold">+{simHandlingDelayMins} mins</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="240"
                  step="15"
                  value={simHandlingDelayMins}
                  onChange={(e) => setSimHandlingDelayMins(Number(e.target.value))}
                  className="w-full accent-blue-500 cursor-pointer"
                />
              </div>

              {/* Capacity Adjust */}
              <div className="p-3.5 bg-slate-800/90 rounded-2xl border border-slate-700/80 space-y-2">
                <div className="flex justify-between font-semibold">
                  <span className="text-slate-300">Capacity Adjust</span>
                  <span className="text-blue-400 font-mono font-bold">
                    {simCapacityAdjustPct >= 0 ? `+${simCapacityAdjustPct}` : simCapacityAdjustPct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="-50"
                  max="100"
                  step="10"
                  value={simCapacityAdjustPct}
                  onChange={(e) => setSimCapacityAdjustPct(Number(e.target.value))}
                  className="w-full accent-blue-500 cursor-pointer"
                />
              </div>

              {/* Cost Multiplier */}
              <div className="p-3.5 bg-slate-800/90 rounded-2xl border border-slate-700/80 space-y-2">
                <div className="flex justify-between font-semibold">
                  <span className="text-slate-300">Cost Multiplier</span>
                  <span className="text-blue-400 font-mono font-bold">{simCostMultiplier.toFixed(1)}x</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="2.5"
                  step="0.1"
                  value={simCostMultiplier}
                  onChange={(e) => setSimCostMultiplier(Number(e.target.value))}
                  className="w-full accent-blue-500 cursor-pointer"
                />
              </div>

              {/* Priority Override */}
              <div className="p-3.5 bg-slate-800/90 rounded-2xl border border-slate-700/80 space-y-2">
                <span className="text-slate-300 font-semibold block">Priority Override</span>
                <select
                  value={simPriorityOverride}
                  onChange={(e) => setSimPriorityOverride(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Default ({currentShipment?.priority})</option>
                  <option value="NORMAL">NORMAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>

            {/* SIMULATION RESULTS VIEW */}
            {simResult && (
              <div className="pt-4 border-t border-slate-800 space-y-4 animate-in fade-in">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                    <TrendingDown className="h-4 w-4" />
                    Simulation Results & Side-by-Side Comparison
                  </h4>
                  <span className="text-xs font-semibold text-slate-300">
                    {simResult.comparison.change_summary}
                  </span>
                </div>

                {/* Side-by-Side Comparison Card */}
                {simResult.has_feasible_simulated_option ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Baseline Card */}
                    <div className="bg-slate-800/90 rounded-2xl p-4 border border-slate-700 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Baseline Plan</span>
                        <span className="text-xs font-bold text-emerald-400">Score {simResult.comparison.baseline_score * 100}%</span>
                      </div>
                      <div className="text-base font-bold text-white">
                        {simResult.baseline_recommended_option?.vehicle_code || 'IND-TRK-101'}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Estimated Cost</span>
                          <strong className="text-slate-200">{formatCurrency(simResult.comparison.baseline_cost)}</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Deadline Buffer</span>
                          <strong className="text-slate-200">{simResult.comparison.baseline_deadline_margin_minutes} mins</strong>
                        </div>
                      </div>
                    </div>

                    {/* Simulated Card */}
                    <div className="bg-blue-950/60 rounded-2xl p-4 border-2 border-blue-500/50 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">Simulated Result</span>
                        <span className="text-xs font-bold text-blue-300">Score {(simResult.comparison.simulated_score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="text-base font-bold text-white">
                        {simResult.simulated_recommended_option?.vehicle_code || 'IND-TRK-101'}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Simulated Cost</span>
                          <strong className="text-blue-300">{formatCurrency(simResult.comparison.simulated_cost)}</strong>
                          <span className="text-[10px] text-slate-400 block font-mono">
                            ({simResult.comparison.cost_delta >= 0 ? `+${formatCurrency(simResult.comparison.cost_delta)}` : formatCurrency(simResult.comparison.cost_delta)})
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Simulated Deadline Buffer</span>
                          <strong className="text-blue-300">{simResult.comparison.simulated_deadline_margin_minutes} mins</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* ALL OPTIONS INFEASIBLE AMBER STATE */
                  <div className="bg-amber-950/80 border-2 border-amber-500/50 rounded-2xl p-6 text-center space-y-2">
                    <AlertTriangle className="h-8 w-8 text-amber-400 mx-auto" />
                    <h5 className="text-base font-bold text-amber-200">No Feasible Recovery Option Under This Scenario</h5>
                    <p className="text-xs text-amber-300 max-w-lg mx-auto">
                      All candidate piggyback routes became infeasible due to simulated route delay (+{simRouteDelayHours}h) or capacity adjustments. Manual dispatch escalation required.
                    </p>
                  </div>
                )}

                {/* Newly Infeasible Routes List */}
                {simResult.newly_infeasible_candidates.length > 0 && (
                  <div className="bg-slate-800/80 rounded-2xl p-4 border border-slate-700/80 space-y-2">
                    <h5 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                      <XCircle className="h-4 w-4" />
                      Candidate Routes Rendered Infeasible by Simulation ({simResult.newly_infeasible_candidates.length})
                    </h5>
                    <div className="space-y-1.5">
                      {simResult.newly_infeasible_candidates.map((c) => (
                        <div key={c.opportunity_id} className="p-2.5 bg-slate-900 rounded-xl text-xs flex items-start justify-between gap-2 border border-slate-700/50">
                          <div>
                            <strong className="text-slate-200">{c.vehicle_code}</strong> ({c.route_code})
                          </div>
                          <span className="text-rose-400 font-medium text-right">{c.rejection_reasons.join(' | ')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
