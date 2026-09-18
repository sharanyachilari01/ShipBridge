import React, { useState } from 'react';
import { Shipment, PiggybackRecommendation } from '../types';
import {
  AlertTriangle,
  ShieldCheck,
  Truck,
  ArrowRight,
  TrendingDown,
  Clock,
  Filter,
  Sparkles,
  MapPin,
  Compass,
  FileText
} from 'lucide-react';

interface RecoveryQueueViewProps {
  shipments: Shipment[];
  recommendations: PiggybackRecommendation[];
  onSelectShipmentId?: (id: number) => void;
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
  onSelectTab: (tab: 'planner' | 'map' | 'detection') => void;
}

export const RecoveryQueueView: React.FC<RecoveryQueueViewProps> = ({
  shipments,
  recommendations,
  onSelectShipmentId,
  onAcceptRecommendation,
  onSelectTab,
}) => {
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'priority' | 'deadline' | 'score' | 'savings'>('priority');

  const misplacedShipments = shipments.filter((s) => s.status === 'MISPLACED');

  const filteredShipments = misplacedShipments.filter((s) => {
    if (priorityFilter === 'ALL') return true;
    if (priorityFilter === 'CRITICAL') return s.priority === 'CRITICAL';
    if (priorityFilter === 'HIGH') return s.priority === 'HIGH';
    if (priorityFilter === 'NORMAL') return s.priority === 'NORMAL';
    return true;
  });

  const getPriorityWeight = (priority: string) => {
    if (priority === 'CRITICAL') return 3;
    if (priority === 'HIGH') return 2;
    return 1;
  };

  // Sort misplaced shipments visibly
  const sortedShipments = [...filteredShipments].sort((a, b) => {
    const recA = recommendations.find((r) => r.shipment.id === a.id);
    const recB = recommendations.find((r) => r.shipment.id === b.id);

    if (sortBy === 'priority') {
      return getPriorityWeight(b.priority) - getPriorityWeight(a.priority);
    }
    if (sortBy === 'deadline') {
      const dateA = a.misplaced_at ? new Date(a.misplaced_at).getTime() : 0;
      const dateB = b.misplaced_at ? new Date(b.misplaced_at).getTime() : 0;
      return dateA - dateB;
    }
    if (sortBy === 'score') {
      const scoreA = recA ? recA.match_score : 0;
      const scoreB = recB ? recB.match_score : 0;
      return scoreB - scoreA;
    }
    if (sortBy === 'savings') {
      const savingsA = recA ? recA.cost_saved : 0;
      const savingsB = recB ? recB.cost_saved : 0;
      return savingsB - savingsA;
    }
    return b.id - a.id;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="p-2.5 bg-rose-100 text-rose-600 rounded-xl">
            <AlertTriangle className="h-6 w-6" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Recovery Queue</h2>
            <p className="text-xs text-slate-500">
              Prioritized misplaced cargo queue & available route piggybacking opportunities.
            </p>
          </div>
        </div>

        {/* Filter & Sort Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Priority Filter */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-500 ml-1.5" />
            <span className="text-slate-600 font-medium">Priority:</span>
            {(['ALL', 'CRITICAL', 'HIGH', 'NORMAL'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                  priorityFilter === p ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Sort By Dropdown/Pills */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-600 font-medium ml-1.5">Sort:</span>
            <button
              onClick={() => setSortBy('priority')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                sortBy === 'priority' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}
            >
              Priority
            </button>
            <button
              onClick={() => setSortBy('score')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                sortBy === 'score' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}
            >
              Match Score
            </button>
            <button
              onClick={() => setSortBy('savings')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                sortBy === 'savings' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}
            >
              Max Savings
            </button>
          </div>
        </div>
      </div>

      {/* Main Queue List */}
      {sortedShipments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm space-y-3">
          <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
            <ShieldCheck className="h-7 w-7" />
          </div>
          <h3 className="text-base font-bold text-slate-900">No Misplaced Cargo in Recovery Queue</h3>
          <p className="text-slate-500 text-xs max-w-md mx-auto">
            All shipments in the Indian logistics network are currently on track.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedShipments.map((shp) => {
            const shipmentRecs = recommendations.filter((r) => r.shipment.id === shp.id);
            const bestRec = shipmentRecs[0] || null;

            return (
              <div
                key={`queue-row-${shp.id}`}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-all"
              >
                {/* Header Information Strip */}
                <div className="p-4 border-b border-slate-100 bg-slate-50/60 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="p-2 bg-rose-500 text-white rounded-xl shadow-sm">
                      <AlertTriangle className="h-5 w-5" />
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-base font-extrabold text-slate-900">
                          {shp.tracking_number}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                            shp.priority === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-700 border border-rose-300'
                              : shp.priority === 'HIGH'
                              ? 'bg-amber-100 text-amber-800 border border-amber-300'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {shp.priority} PRIORITY
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-0.5">
                        Origin: <strong>{shp.origin_hub?.name || 'Bengaluru'}</strong> &rarr; Current:{' '}
                        <strong>{shp.expected_next_hub?.name || 'Hyderabad'}</strong> &rarr; Target:{' '}
                        <strong>{shp.destination_hub?.name || 'Delhi'}</strong>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-600">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Weight / Volume</span>
                      <strong className="text-slate-800">{shp.weight_kg} kg | {shp.volume_m3 || 1.0} m³</strong>
                    </div>
                    <div className="h-8 w-px bg-slate-200" />
                    <div>
                      <span className="text-slate-400 block text-[10px]">Status / Options</span>
                      <span className="font-bold text-slate-900">
                        {shipmentRecs.length > 0 ? `${shipmentRecs.length} Option(s)` : 'No Piggyback Option'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Recommendations or Explanatory No-Option Card */}
                <div className="p-4 space-y-3">
                  {shipmentRecs.length > 0 ? (
                    <div className="space-y-2">
                      {shipmentRecs.map((rec) => (
                        <div
                          key={`rec-item-${rec.recommendation_id}`}
                          className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 hover:border-emerald-300 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                        >
                          <div className="space-y-1 max-w-xl">
                            <div className="flex items-center gap-2">
                              <span className="bg-emerald-600 text-white font-extrabold text-[10px] px-2 py-0.5 rounded-full">
                                {rec.match_score}% Match Score
                              </span>
                              <span className="font-bold text-xs text-slate-900 flex items-center gap-1">
                                <Truck className="h-3.5 w-3.5 text-blue-600" />
                                {rec.vehicle_route.vehicle_code} ({rec.vehicle_route.vehicle_type})
                              </span>
                            </div>

                            <p className="text-xs text-slate-700 bg-white p-2 rounded-lg border border-slate-200/80">
                              {rec.explanation}
                            </p>

                            <div className="flex items-center gap-3 text-[11px] font-semibold text-emerald-700">
                              <span>Save ₹{rec.cost_saved.toLocaleString()} vs dedicated truck</span>
                              <span>•</span>
                              <span>Offset {rec.co2_saved_kg} kg CO2</span>
                            </div>
                          </div>

                          <button
                            onClick={() => onAcceptRecommendation(rec)}
                            className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2 px-3 rounded-xl shadow-sm flex items-center justify-center gap-1 transition-colors whitespace-nowrap"
                          >
                            <ShieldCheck className="h-4 w-4" />
                            Accept Piggyback
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3.5 bg-rose-50/60 rounded-xl border border-rose-200/70 text-xs text-rose-900 flex items-start gap-2.5">
                      <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold block">No Piggyback Recovery Route Currently Available</span>
                        <p className="text-rose-800 text-[11px] mt-0.5">
                          No active truck passing through this corridor has sufficient available weight ({shp.weight_kg}kg) or volume ({shp.volume_m3 || 1.0}m³) capacity meeting delivery SLA.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Actions Bar per Row */}
                  <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs">
                    <button
                      onClick={() => onSelectShipmentId?.(shp.id)}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-3 py-1.5 rounded-lg border border-slate-200 flex items-center gap-1"
                    >
                      <MapPin className="h-3.5 w-3.5 text-blue-600" /> Open on Map
                    </button>

                    <button
                      onClick={() => onSelectTab('planner')}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-3 py-1.5 rounded-lg border border-slate-200 flex items-center gap-1"
                    >
                      <Compass className="h-3.5 w-3.5 text-blue-600" /> Open Planner
                    </button>

                    <button
                      onClick={() => onSelectTab('detection')}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-3 py-1.5 rounded-lg border border-slate-200 flex items-center gap-1"
                    >
                      <FileText className="h-3.5 w-3.5 text-slate-600" /> View Detection Evidence
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
