import React, { useState } from 'react';
import { Shipment, PiggybackRecommendation } from '../types';
import {
  AlertTriangle,
  ShieldCheck,
  Truck,
  ArrowRight,
  TrendingDown,
  Leaf,
  Clock,
  Filter,
  Layers,
  Sparkles
} from 'lucide-react';

interface RecoveryQueueViewProps {
  shipments: Shipment[];
  recommendations: PiggybackRecommendation[];
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
  onSelectTab: (tab: 'planner' | 'map') => void;
}

export const RecoveryQueueView: React.FC<RecoveryQueueViewProps> = ({
  shipments,
  recommendations,
  onAcceptRecommendation,
  onSelectTab,
}) => {
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'score' | 'savings'>('score');

  const misplacedShipments = shipments.filter((s) => s.status === 'MISPLACED');

  const filteredShipments = misplacedShipments.filter((s) => {
    if (priorityFilter === 'ALL') return true;
    return s.priority === priorityFilter;
  });

  // Sort recommendations
  const sortedRecommendations = [...recommendations].sort((a, b) => {
    if (sortBy === 'score') return b.match_score - a.match_score;
    return b.cost_saved - a.cost_saved;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-rose-100 text-rose-600 rounded-xl">
              <AlertTriangle className="h-6 w-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Shipment Recovery Queue</h2>
              <p className="text-sm text-slate-500">
                Identify misplaced cargo and review piggyback opportunities on active transport legs.
              </p>
            </div>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-500 ml-2" />
            <span className="text-slate-600 font-medium">Priority:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'NORMAL'].map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                  priorityFilter === p
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-600 font-medium ml-2">Sort:</span>
            <button
              onClick={() => setSortBy('score')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                sortBy === 'score' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}
            >
              Match Score
            </button>
            <button
              onClick={() => setSortBy('savings')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                sortBy === 'savings' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}
            >
              Max Savings
            </button>
          </div>
        </div>
      </div>

      {/* Main Queue Content */}
      {filteredShipments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <ShieldCheck className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Misplaced Shipments in Queue</h3>
          <p className="text-slate-500 text-sm max-w-md mx-auto mt-1">
            All shipments in the regional network are currently on track. You can add a new test shipment or simulate misplacement to test piggybacking.
          </p>
          <button
            onClick={() => onSelectTab('map')}
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-xl text-sm shadow-sm inline-flex items-center gap-2"
          >
            View Live Network Map <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredShipments.map((shp) => {
            // Find recommendations matching this shipment
            const shipmentRecs = sortedRecommendations.filter((r) => r.shipment.id === shp.id);

            return (
              <div
                key={`queue-item-${shp.id}`}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Shipment Info Bar */}
                <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="p-2.5 bg-rose-500 text-white rounded-xl shadow-sm">
                      <AlertTriangle className="h-5 w-5" />
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-base font-bold text-slate-900">
                          {shp.tracking_number}
                        </span>
                        <span
                          className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
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
                      <p className="text-xs text-slate-500 mt-0.5">
                        Current Hub: <strong className="text-slate-800">{shp.current_hub?.name || 'St. Louis Terminal'}</strong> &rarr; Target:{' '}
                        <strong className="text-slate-800">{shp.destination_hub?.name || 'Chicago Central'}</strong>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-600">
                    <div>
                      <span className="text-slate-400 block">Cargo Weight</span>
                      <strong className="text-slate-800">{shp.weight_kg} kg</strong>
                    </div>
                    <div className="h-8 w-px bg-slate-200" />
                    <div>
                      <span className="text-slate-400 block">Volume</span>
                      <strong className="text-slate-800">{shp.volume_m3} m³</strong>
                    </div>
                  </div>
                </div>

                {/* Notes / Context */}
                {shp.notes && (
                  <div className="px-5 py-2.5 bg-rose-50/60 border-b border-rose-100/50 text-xs text-rose-900 flex items-center gap-2">
                    <span className="font-semibold">Misplacement Log:</span> {shp.notes}
                  </div>
                )}

                {/* Piggyback Recommendations List */}
                <div className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Sparkles className="h-4 w-4 text-emerald-600" />
                      Piggyback Recovery Options ({shipmentRecs.length} Candidate Routes Found)
                    </h4>
                  </div>

                  {shipmentRecs.length === 0 ? (
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 text-center">
                      No matching active routes with available capacity passing through this corridor right now.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      {shipmentRecs.map((rec) => (
                        <div
                          key={rec.recommendation_id}
                          className="bg-slate-50 rounded-xl p-4 border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/30 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                        >
                          <div className="space-y-2 max-w-2xl">
                            {/* Score & Vehicle title */}
                            <div className="flex items-center gap-2">
                              <span className="bg-emerald-600 text-white font-extrabold text-xs px-2.5 py-0.5 rounded-full shadow-sm">
                                {rec.match_score}% Match
                              </span>
                              <span className="font-bold text-sm text-slate-900 flex items-center gap-1">
                                <Truck className="h-4 w-4 text-blue-600" />
                                {rec.vehicle_route.vehicle_code} ({rec.vehicle_route.vehicle_type})
                              </span>
                              <span className="text-xs text-slate-500">
                                Driver: <strong>{rec.vehicle_route.driver_name}</strong>
                              </span>
                            </div>

                            {/* Natural Language Explanation */}
                            <p className="text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-slate-200/80 leading-relaxed">
                              {rec.explanation}
                            </p>

                            {/* Savings Pills */}
                            <div className="flex items-center gap-3 text-xs">
                              <span className="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                <TrendingDown className="h-3.5 w-3.5" />
                                Save ${rec.cost_saved} vs Dedicated Truck
                              </span>
                              <span className="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                <Leaf className="h-3.5 w-3.5" />
                                Offset {rec.co2_saved_kg} kg CO2
                              </span>
                              <span className="text-slate-500">
                                Remaining Capacity: <strong>{rec.spare_capacity_after_kg} kg</strong>
                              </span>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="flex flex-col sm:flex-row md:flex-col gap-2 w-full md:w-auto min-w-[200px]">
                            <button
                              onClick={() => onAcceptRecommendation(rec)}
                              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow-sm flex items-center justify-center gap-1.5 transition-colors"
                            >
                              <ShieldCheck className="h-4 w-4" />
                              Accept Piggyback
                            </button>

                            <button
                              onClick={() => onSelectTab('planner')}
                              className="w-full bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium text-xs py-2 px-3 rounded-xl transition-colors text-center"
                            >
                              Compare in Planner
                            </button>

                            {/* Disabled button explicitly labeled Coming Soon as per guidelines */}
                            <button
                              disabled
                              className="w-full bg-slate-100 text-slate-400 font-medium text-[11px] py-1.5 px-2 rounded-xl border border-slate-200 text-center cursor-not-allowed"
                            >
                              Dispatch Dedicated Recovery (Coming soon)
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
