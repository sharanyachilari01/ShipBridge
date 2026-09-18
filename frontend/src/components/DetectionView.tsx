import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Radio,
  CheckCircle2,
  XCircle,
  Clock,
  Compass,
  MapPin,
  Truck,
  Activity,
  ArrowRight,
  Info
} from 'lucide-react';
import { DemoShipmentAnalysis } from '../types';
import { fetchDemoShipmentsAnalysis } from '../api';

export const DetectionView: React.FC = () => {
  const [demoCases, setDemoCases] = useState<DemoShipmentAnalysis[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('SH009');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDemoCases();
  }, []);

  const loadDemoCases = async () => {
    try {
      setLoading(true);
      const data = await fetchDemoShipmentsAnalysis();
      setDemoCases(data);
    } catch (err) {
      console.error('Failed to load demo detection cases', err);
      setError('Could not connect to detection engine backend.');
    } finally {
      setLoading(false);
    }
  };

  const activeCase = demoCases.find((c) => c.shipment_id === selectedCaseId) || demoCases[0];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'MISPLACED':
        return {
          label: 'MISPLACED',
          bg: 'bg-red-100 text-red-800 border-red-300',
          icon: ShieldAlert,
          color: 'text-red-600',
        };
      case 'SUSPICIOUS':
        return {
          label: 'SUSPICIOUS',
          bg: 'bg-amber-100 text-amber-800 border-amber-300',
          icon: AlertTriangle,
          color: 'text-amber-600',
        };
      case 'NORMAL_REROUTED':
        return {
          label: 'NORMAL_REROUTED',
          bg: 'bg-blue-100 text-blue-800 border-blue-300',
          icon: CheckCircle2,
          color: 'text-blue-600',
        };
      case 'DELAYED':
        return {
          label: 'DELAYED',
          bg: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          icon: Clock,
          color: 'text-yellow-600',
        };
      case 'UNKNOWN_SIGNAL_MONITOR':
        return {
          label: 'UNKNOWN_SIGNAL_MONITOR',
          bg: 'bg-slate-200 text-slate-800 border-slate-300',
          icon: Radio,
          color: 'text-slate-600',
        };
      case 'NORMAL':
      default:
        return {
          label: 'NORMAL',
          bg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          icon: ShieldCheck,
          color: 'text-emerald-600',
        };
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.65) return 'text-red-600 bg-red-50 border-red-200';
    if (score >= 0.40) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-emerald-600 bg-emerald-50 border-emerald-200';
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)] text-slate-500">
        <Activity className="h-8 w-8 animate-spin text-blue-600 mb-3" />
        <p className="font-medium text-slate-700">Executing Stage 1 Evidence-Based Detection Engine...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-lg border border-slate-800">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 bg-blue-500/20 text-blue-300 text-xs font-semibold px-3 py-1 rounded-full border border-blue-500/30 mb-2">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>Stage 1 Module — Evidence-Based Detection</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Misplaced Shipment Detection Module
            </h1>
            <p className="text-slate-400 text-sm mt-1 max-w-3xl">
              Evaluates telemetry streams against 7 false-positive safeguards, corridor geometries, trajectory persistence, and BLE gateway bindings using evidence-based classification rules.
            </p>
          </div>
          <button
            onClick={loadDemoCases}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-4 py-2.5 rounded-xl transition shadow"
          >
            <Activity className="h-4 w-4" />
            <span>Re-evaluate All 10 Cases</span>
          </button>
        </div>

        {/* Status Taxonomy Counter Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mt-6 pt-6 border-t border-slate-800">
          <div className="bg-red-950/40 border border-red-800/50 p-3 rounded-xl">
            <span className="text-xs text-red-300 font-medium">MISPLACED</span>
            <p className="text-2xl font-bold text-red-400">
              {demoCases.filter((c) => c.current_status === 'MISPLACED').length}
            </p>
          </div>
          <div className="bg-amber-950/40 border border-amber-800/50 p-3 rounded-xl">
            <span className="text-xs text-amber-300 font-medium">SUSPICIOUS</span>
            <p className="text-2xl font-bold text-amber-400">
              {demoCases.filter((c) => c.current_status === 'SUSPICIOUS').length}
            </p>
          </div>
          <div className="bg-blue-950/40 border border-blue-800/50 p-3 rounded-xl">
            <span className="text-xs text-blue-300 font-medium">NORMAL_REROUTED</span>
            <p className="text-2xl font-bold text-blue-400">
              {demoCases.filter((c) => c.current_status === 'NORMAL_REROUTED').length}
            </p>
          </div>
          <div className="bg-yellow-950/40 border border-yellow-800/50 p-3 rounded-xl">
            <span className="text-xs text-yellow-300 font-medium">DELAYED</span>
            <p className="text-2xl font-bold text-yellow-400">
              {demoCases.filter((c) => c.current_status === 'DELAYED').length}
            </p>
          </div>
          <div className="bg-slate-800 border border-slate-700 p-3 rounded-xl">
            <span className="text-xs text-slate-300 font-medium">UNKNOWN_SIGNAL</span>
            <p className="text-2xl font-bold text-slate-300">
              {demoCases.filter((c) => c.current_status === 'UNKNOWN_SIGNAL_MONITOR').length}
            </p>
          </div>
          <div className="bg-emerald-950/40 border border-emerald-800/50 p-3 rounded-xl">
            <span className="text-xs text-emerald-300 font-medium">NORMAL</span>
            <p className="text-2xl font-bold text-emerald-400">
              {demoCases.filter((c) => c.current_status === 'NORMAL').length}
            </p>
          </div>
        </div>
      </div>

      {/* Controlled Scenarios Grid */}
      <div>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Controlled Scenario Test Bench (SH001 to SH010)
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-5 md:grid-cols-10 gap-2">
          {demoCases.map((c) => {
            const isSelected = c.shipment_id === selectedCaseId;
            const badge = getStatusBadge(c.current_status);
            return (
              <button
                key={c.shipment_id}
                onClick={() => setSelectedCaseId(c.shipment_id)}
                className={`flex flex-col items-center p-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50/80 shadow-md ring-2 ring-blue-500/20'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <span className="font-mono text-xs font-bold text-slate-800">{c.shipment_id}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md mt-1 border ${badge.bg}`}>
                  {c.current_status === 'UNKNOWN_SIGNAL_MONITOR' ? 'UNKNOWN' : c.current_status}
                </span>
                <span className="text-[10px] font-mono text-slate-500 mt-1">
                  Score: {c.misplacement_score.toFixed(2)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Scenario Active Evaluation Card */}
      {activeCase && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Evidence Classification Column */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-xl font-bold text-slate-900">{activeCase.tracking_number}</h3>
                    <span className="font-mono text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      {activeCase.shipment_id}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                    <MapPin className="h-3.5 w-3.5 text-slate-400" />
                    <span>{activeCase.origin_hub}</span>
                    <ArrowRight className="h-3 w-3 text-slate-400" />
                    <span>{activeCase.destination_hub}</span>
                  </p>
                </div>

                {/* Status Badge */}
                {(() => {
                  const badge = getStatusBadge(activeCase.current_status);
                  const Icon = badge.icon;
                  return (
                    <div className={`flex items-center space-x-2 px-4 py-2 rounded-xl border font-bold text-sm ${badge.bg}`}>
                      <Icon className="h-5 w-5" />
                      <span>{badge.label}</span>
                    </div>
                  );
                })()}
              </div>

              {/* Evidence-Based Explanation Callout */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                <div className="flex items-start space-x-3">
                  <Info className="h-5 w-5 text-blue-600 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Evidence-Based Classification Explanation
                    </h4>
                    <p className="text-sm text-slate-800 leading-relaxed">
                      {activeCase.explanation}
                    </p>
                    <p className="text-xs text-slate-500 mt-2 italic">
                      Primary Cause Code: <span className="font-mono font-medium text-slate-700">{activeCase.primary_cause}</span>
                    </p>
                  </div>
                </div>
              </div>

              {/* Key Metrics Dashboard */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className={`p-4 rounded-xl border ${getScoreColor(activeCase.misplacement_score)}`}>
                  <span className="text-xs font-semibold text-slate-500 block">Misplacement Score</span>
                  <span className="text-2xl font-bold">{activeCase.misplacement_score.toFixed(2)}</span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Threshold: 0.65</span>
                </div>

                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                  <span className="text-xs font-semibold text-slate-500 block">Corridor Deviation</span>
                  <span className="text-2xl font-bold text-slate-800">
                    {activeCase.distance_to_nearest_valid_route_km.toFixed(1)} km
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Max allowed: 15.0 km</span>
                </div>

                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                  <span className="text-xs font-semibold text-slate-500 block">Heading Difference</span>
                  <span className="text-2xl font-bold text-slate-800">
                    {activeCase.heading_difference_deg.toFixed(1)}°
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Vector vs Corridor</span>
                </div>

                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                  <span className="text-xs font-semibold text-slate-500 block">Persistence</span>
                  <span className={`text-xl font-bold ${activeCase.persistent_anomaly ? 'text-red-600' : 'text-slate-700'}`}>
                    {activeCase.persistent_anomaly ? 'PERSISTENT' : 'TRANSIENT'}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">
                    {activeCase.telemetry_points_count} points evaluated
                  </span>
                </div>
              </div>
            </div>

            {/* Controlled Case Details Box */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <Truck className="h-4 w-4 text-blue-600" />
                <span>Shipment & Telemetry Metadata</span>
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-slate-600 bg-slate-50 p-4 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[10px]">ASSIGNED VEHICLE</span>
                  <span className="font-semibold text-slate-800">{activeCase.assigned_vehicle}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">LAST LAT / LNG</span>
                  <span className="font-mono text-slate-800">{activeCase.current_lat.toFixed(4)}, {activeCase.current_lng.toFixed(4)}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">CURRENT SPEED</span>
                  <span className="font-semibold text-slate-800">{activeCase.speed_kmh} km/h</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">NEXT EXPECTED HUB</span>
                  <span className="font-semibold text-slate-800">{activeCase.expected_next_hub}</span>
                </div>
              </div>
            </div>
          </div>

          {/* 7 False-Positive Safeguards Checklist Column */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-blue-600" />
                  <span>7 False-Positive Safeguards</span>
                </h3>
                <span className="text-[10px] font-semibold bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
                  Audit Checklist
                </span>
              </div>

              <div className="space-y-3">
                {/* 1. Approved Reroute Present */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">1. Approved Reroute</span>
                    <span className="text-[11px] text-slate-500">Active approved reroute override</span>
                  </div>
                  {activeCase.safeguard_outcomes.approved_reroute_present ? (
                    <span className="flex items-center text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-200">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> ACTIVE
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-slate-400">NONE</span>
                  )}
                </div>

                {/* 2. Vehicle Transfer Active */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">2. Vehicle Transfer</span>
                    <span className="text-[11px] text-slate-500">Hub transfer &lt;15m grace</span>
                  </div>
                  {activeCase.safeguard_outcomes.vehicle_transfer_active ? (
                    <span className="flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> IN GRACE
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-slate-400">INACTIVE</span>
                  )}
                </div>

                {/* 3. Traffic Delay Only */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">3. Traffic Delay Only</span>
                    <span className="text-[11px] text-slate-500">Delayed on valid corridor</span>
                  </div>
                  {activeCase.safeguard_outcomes.traffic_delay_only ? (
                    <span className="flex items-center text-xs font-bold text-yellow-600 bg-yellow-50 px-2 py-1 rounded border border-yellow-200">
                      <Clock className="h-3.5 w-3.5 mr-1" /> DELAYED
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-slate-400">NO DELAY</span>
                  )}
                </div>

                {/* 4. Signal Loss Only */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">4. Telemetry Signal Loss</span>
                    <span className="text-[11px] text-slate-500">Missing signal &gt;3 hours</span>
                  </div>
                  {activeCase.safeguard_outcomes.signal_loss_only ? (
                    <span className="flex items-center text-xs font-bold text-slate-700 bg-slate-200 px-2 py-1 rounded border border-slate-300">
                      <Radio className="h-3.5 w-3.5 mr-1" /> SIGNAL LOST
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-emerald-600 font-semibold">SIGNAL OK</span>
                  )}
                </div>

                {/* 5. GPS Accuracy Valid */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">5. GPS Accuracy</span>
                    <span className="text-[11px] text-slate-500">Precision threshold &le;50m</span>
                  </div>
                  {activeCase.safeguard_outcomes.gps_accuracy_valid ? (
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                      VALID (&le;50m)
                    </span>
                  ) : (
                    <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded border border-red-200">
                      POOR (&gt;50m)
                    </span>
                  )}
                </div>

                {/* 6. On Allowed Alt Route */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">6. Allowed Alternative</span>
                    <span className="text-[11px] text-slate-500">Valid secondary corridor match</span>
                  </div>
                  {activeCase.safeguard_outcomes.on_allowed_alternative_route ? (
                    <span className="flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> MATCHED
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-slate-400">UNMATCHED</span>
                  )}
                </div>

                {/* 7. Low Speed Heading Ignored */}
                <div className="flex items-start justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                  <div>
                    <span className="text-xs font-semibold text-slate-800 block">7. Low-Speed Cutoff</span>
                    <span className="text-[11px] text-slate-500">Speed &le;20 km/h heading ignored</span>
                  </div>
                  {activeCase.safeguard_outcomes.low_speed_heading_ignored ? (
                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-200">
                      IGNORED (&le;20km/h)
                    </span>
                  ) : (
                    <span className="text-xs font-medium text-slate-400">EVALUATED</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
