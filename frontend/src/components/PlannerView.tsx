import React, { useState, useEffect } from 'react';
import { Shipment, VehicleRoute, PiggybackRecommendation, SimulationResult, Stage2PiggybackOption } from '../types';
import { simulateRecovery, fetchRecoveryOptions } from '../api';
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
  Play,
  Check,
  X
} from 'lucide-react';

interface PlannerViewProps {
  shipments: Shipment[];
  routes: VehicleRoute[];
  recommendations: PiggybackRecommendation[];
  selectedShipmentId?: number | null;
  onSelectShipmentId?: (id: number) => void;
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
}

export const PlannerView: React.FC<PlannerViewProps> = ({
  shipments,
  recommendations,
  selectedShipmentId,
  onSelectShipmentId,
  onAcceptRecommendation,
}) => {
  const misplacedShipments = shipments.filter((s) => s.status === 'MISPLACED');
  
  const defaultShipment = misplacedShipments.find((s) => s.id === 9) || misplacedShipments[0] || null;
  const [activeShipmentId, setActiveShipmentId] = useState<number>(
    selectedShipmentId || defaultShipment?.id || 1
  );

  const currentShipment = misplacedShipments.find((s) => s.id === activeShipmentId) || defaultShipment || null;
  const rawRec = recommendations.find((r) => r.shipment.id === activeShipmentId) || null;

  // Additional options from backend
  const [stage2Options, setStage2Options] = useState<Stage2PiggybackOption[]>([]);
  const [selectedOppId, setSelectedOppId] = useState<number | null>(null);
  const [loadingOptions, setLoadingOptions] = useState<boolean>(true);

  // Dispatcher decision Modal / State
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [dispatcherName, setDispatcherName] = useState<string>('Lead Logistics Dispatcher');
  const [decisionSuccessMsg, setDecisionSuccessMsg] = useState<string | null>(null);

  // What-If Simulation Inputs
  const [simRouteDelayHours, setSimRouteDelayHours] = useState<number>(0);
  const [simHandlingDelayMins, setSimHandlingDelayMins] = useState<number>(0);
  const [simCapacityAdjustPct, setSimCapacityAdjustPct] = useState<number>(0);
  const [simCostMultiplier, setSimCostMultiplier] = useState<number>(1.0);
  const [simPriorityOverride, setSimPriorityOverride] = useState<string>('');
  const [simTransferHub, setSimTransferHub] = useState<string>('');

  // Simulation execution state
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  // Fetch Stage 2 options when active shipment changes
  useEffect(() => {
    if (currentShipment) {
      setLoadingOptions(true);
      setStage2Options([]);
      setSelectedOppId(null);
      handleResetSimulation();

      fetchRecoveryOptions(currentShipment.id)
        .then((res) => {
          const feasibleOpts = (res.opportunities || []).filter(
            (o) => o.is_feasible !== false
          );
          setStage2Options(feasibleOpts);
          if (feasibleOpts.length > 0) {
            setSelectedOppId(feasibleOpts[0].vehicle_id);
          }
        })
        .catch(() => setStage2Options([]))
        .finally(() => setLoadingOptions(false));
    }
  }, [activeShipmentId]);

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
        transfer_hub_unavailable: simTransferHub ? simTransferHub : undefined,
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
    setSimTransferHub('');
    setSimResult(null);
    setSimError(null);
  };

  const handleApproveOption = async (opp?: Stage2PiggybackOption | null) => {
    if (!currentShipment || !rawRec) return;
    try {
      const res = await fetch(`/api/recovery/recommendations/${rawRec.recommendation_id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dispatcher_name: dispatcherName,
          decision_note: opp ? `Dispatcher approved alternative vehicle ${opp.vehicle_code}` : 'Dispatcher approved top system recommendation',
          selected_opportunity_id: opp ? opp.vehicle_id : undefined,
        }),
      });
      if (res.ok) {
        setDecisionSuccessMsg(`Recovery plan approved by ${dispatcherName}! Shipment status set to RECOVERY_APPROVED.`);
        onAcceptRecommendation(rawRec);
      }
    } catch (err) {
      console.error('Approval failed:', err);
    }
  };

  const handleRejectRecommendation = async () => {
    if (!currentShipment || !rawRec || !rejectReason.trim()) return;
    try {
      const res = await fetch(`/api/recovery/recommendations/${rawRec.recommendation_id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dispatcher_name: dispatcherName,
          decision_note: rejectReason.trim(),
        }),
      });
      if (res.ok) {
        setShowRejectModal(false);
        setDecisionSuccessMsg(`Recommendation rejected by ${dispatcherName}. Shipment remains in queue for future re-evaluation.`);
      }
    } catch (err) {
      console.error('Rejection failed:', err);
    }
  };

  const formatCurrency = (val: number) => `₹${Math.round(val).toLocaleString()}`;

  const hasFeasibleOptions = stage2Options.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="p-2.5 bg-blue-100 text-blue-600 rounded-xl">
            <Compass className="h-6 w-6" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Recovery Planner & Dispatcher Control</h2>
            <p className="text-xs text-slate-500">
              Review multi-hop recovery options, dispatcher choice, and run What-if simulations.
            </p>
          </div>
        </div>
      </div>

      {decisionSuccessMsg && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-4 text-xs font-bold text-emerald-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <span>{decisionSuccessMsg}</span>
          </div>
          <button onClick={() => setDecisionSuccessMsg(null)} className="text-emerald-700 hover:text-emerald-900">✕</button>
        </div>
      )}

      {misplacedShipments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm space-y-3">
          <ShieldCheck className="h-10 w-10 text-emerald-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">All Shipments On Track</h3>
          <p className="text-xs text-slate-500">There are currently no misplaced shipments requiring recovery evaluation.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Shipment Selector & Specs */}
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

          {/* PRIMARY HERO CARD & STATE RESOLUTION */}
          <div>
            {loadingOptions ? (
              <div className="bg-slate-900 text-white rounded-3xl p-8 text-center space-y-3 border border-slate-800 shadow-xl">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
                <p className="text-xs font-semibold text-slate-300">
                  Analyzing recovery corridor feasibility for shipment {currentShipment?.tracking_number}...
                </p>
              </div>
            ) : hasFeasibleOptions ? (
              <div className="bg-gradient-to-br from-blue-900 via-slate-900 to-emerald-950 text-white rounded-3xl p-6 sm:p-8 shadow-xl border-2 border-emerald-400/50 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
                  <div className="flex items-center gap-3">
                    <span className="p-3 bg-emerald-500/20 text-emerald-400 rounded-2xl border border-emerald-400/30">
                      <Sparkles className="h-7 w-7" />
                    </span>
                    <div>
                      <span className="text-xs uppercase tracking-widest font-extrabold text-emerald-400 block">
                        Top System Recommendation #1
                      </span>
                      <h3 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
                        {rawRec?.vehicle_route?.vehicle_code || stage2Options[0]?.vehicle_code || 'IND-TRK-101'} — {rawRec?.vehicle_route?.vehicle_type || 'Active Carrier'}
                      </h3>
                      <p className="text-xs text-slate-300 mt-0.5">
                        Pickup: <strong>{stage2Options[0]?.pickup_hub_name || rawRec?.pickup_hub?.name || 'Pickup Hub'}</strong> → Drop: <strong>{stage2Options[0]?.drop_hub_name || rawRec?.dropoff_hub?.name || 'Destination Hub'}</strong>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-[10px] uppercase text-slate-400 font-bold block">Selection Score</span>
                      <span className="text-2xl font-black text-emerald-400">
                        {rawRec?.match_score ? `${rawRec.match_score}%` : `${Math.round((stage2Options[0]?.piggyback_score || 0.9) * 100)}%`}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Rationale & Action Buttons */}
                <div className="p-4 bg-white/5 rounded-2xl border border-white/10 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Info className="h-4 w-4 text-emerald-400" />
                    Deterministic Selection Rationale
                  </h4>
                  <p className="text-xs text-slate-200 leading-relaxed font-medium">
                    {stage2Options[0]?.explanation || rawRec?.explanation || 'Direct piggyback connection along primary highway corridor.'}
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                  <button
                    onClick={() => handleApproveOption(stage2Options[0])}
                    className="w-full sm:flex-1 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-extrabold text-sm py-3.5 px-6 rounded-2xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all"
                  >
                    <ShieldCheck className="h-5 w-5" />
                    Approve Top System Recommendation
                  </button>

                  <button
                    onClick={() => setShowRejectModal(true)}
                    className="w-full sm:w-auto bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-400/40 font-bold text-xs py-3.5 px-5 rounded-2xl flex items-center justify-center gap-1.5 transition-all"
                  >
                    <X className="h-4 w-4" />
                    Reject Recommendation
                  </button>
                </div>
              </div>
            ) : (
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

                <div className="p-4 bg-amber-500/10 rounded-2xl border border-amber-500/30 text-xs text-amber-100 font-medium space-y-2">
                  <span className="font-bold block text-amber-300">Aggregated Feasibility Rejection Reasons:</span>
                  <ul className="list-disc list-inside space-y-1 text-amber-100">
                    <li>SLA Delivery Deadline Constraint: Active trucks passing through corridor exceed deadline.</li>
                    <li>Payload Capacity Bottleneck: Cargo weight ({currentShipment?.weight_kg}kg) or volume ({currentShipment?.volume_m3 || 1.0}m³) exceeds available space.</li>
                    <li>Route Incompatibility: No direct or hub-transfer route matches the current deviation vector.</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* RANKED ALTERNATIVE OPTIONS (Rendered ONLY when feasible options exist > 1) */}
          {hasFeasibleOptions && stage2Options.length > 1 && (
            <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Truck className="h-4 w-4 text-blue-600" />
                Ranked Alternative Feasible Recovery Options ({stage2Options.length - 1})
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {stage2Options.slice(1).map((opt, idx) => (
                  <div
                    key={`opt-alt-${opt.candidate_id}`}
                    className="p-4 rounded-2xl border bg-slate-50 border-slate-200 hover:border-blue-300 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-slate-900">
                        Option #{idx + 2}: {opt.vehicle_code}
                      </span>
                      <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                        {opt.transfer_complexity}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {opt.explanation}
                    </p>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-200 text-xs">
                      <span className="font-bold text-slate-800">{formatCurrency(opt.estimated_total_cost)}</span>
                      <button
                        onClick={() => handleApproveOption(opt)}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-3 py-1.5 rounded-lg flex items-center gap-1 shadow-sm"
                      >
                        <Check className="h-3.5 w-3.5" /> Approve This Option
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* WHAT-IF SIMULATOR SECTION */}
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
                      Simulation only — zero MySQL mutations
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Test route delays, capacity adjustments, and hub closure disruptions in real-time.
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

            {/* Slider & Dropdown Inputs Grid */}
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

              {/* Transfer Delay */}
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

              {/* Hub Closure Simulation */}
              <div className="p-3.5 bg-slate-800/90 rounded-2xl border border-slate-700/80 space-y-2">
                <span className="text-slate-300 font-semibold block">Simulate Hub Closure</span>
                <select
                  value={simTransferHub}
                  onChange={(e) => setSimTransferHub(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">None (All Hubs Open)</option>
                  <option value="HUB-HYD">HUB-HYD (Hyderabad)</option>
                  <option value="HUB-LKO">HUB-LKO (Lucknow)</option>
                  <option value="HUB-NAG">HUB-NAG (Nagpur)</option>
                  <option value="HUB-BOM">HUB-BOM (Mumbai)</option>
                </select>
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

                {simResult.has_feasible_simulated_option ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Simulated Deadline Buffer</span>
                          <strong className="text-blue-300">{simResult.comparison.simulated_deadline_margin_minutes} mins</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-amber-950/80 border-2 border-amber-500/50 rounded-2xl p-6 text-center space-y-2">
                    <AlertTriangle className="h-8 w-8 text-amber-400 mx-auto" />
                    <h5 className="text-base font-bold text-amber-200">No Feasible Recovery Option Under This Scenario</h5>
                    <p className="text-xs text-amber-300 max-w-lg mx-auto">
                      All candidate piggyback routes became infeasible due to simulated route delay (+{simRouteDelayHours}h) or hub closure ({simTransferHub || 'simulated'}).
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* DISPATCHER REJECTION MODAL */}
      {showRejectModal && (
        <div className="fixed inset-0 z-[1000] bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-rose-500" />
                Reject System Recovery Plan
              </h3>
              <button onClick={() => setShowRejectModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">✕</button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Dispatcher Name:</label>
                <input
                  type="text"
                  value={dispatcherName}
                  onChange={(e) => setDispatcherName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-bold"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  Rejection Reason (Mandatory Note):
                </label>
                <textarea
                  rows={3}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="State operational rationale for rejecting recommendation..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2.5 rounded-xl text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectRecommendation}
                disabled={!rejectReason.trim()}
                className="flex-1 bg-rose-600 hover:bg-rose-700 text-white font-bold py-2.5 rounded-xl text-xs disabled:opacity-50"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
