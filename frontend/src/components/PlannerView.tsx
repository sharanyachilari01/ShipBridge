import React, { useState } from 'react';
import { Shipment, VehicleRoute, PiggybackRecommendation } from '../types';
import { Compass, Truck, ShieldCheck, DollarSign, Leaf, AlertCircle, ArrowRight } from 'lucide-react';

interface PlannerViewProps {
  shipments: Shipment[];
  routes: VehicleRoute[];
  recommendations: PiggybackRecommendation[];
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
}

export const PlannerView: React.FC<PlannerViewProps> = ({
  shipments,
  recommendations,
  onAcceptRecommendation,
}) => {
  const misplacedShipments = shipments.filter((s) => s.status === 'MISPLACED');
  const [selectedShipmentId, setSelectedShipmentId] = useState<number>(
    misplacedShipments[0]?.id || 0
  );

  const currentShipment = misplacedShipments.find((s) => s.id === selectedShipmentId);
  const currentRec = recommendations.find((r) => r.shipment.id === selectedShipmentId);

  // Default comparison numbers if no active recommendation
  const dedicatedCost = currentRec ? currentRec.cost_saved + 45 : 450;
  const dedicatedCO2 = currentRec ? currentRec.co2_saved_kg : 180;
  const piggybackCost = 45;
  const piggybackCO2 = 0; // 0 incremental CO2

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex items-center gap-3">
          <span className="p-2.5 bg-blue-100 text-blue-600 rounded-xl">
            <Compass className="h-6 w-6" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Recovery Trade-off Planner</h2>
            <p className="text-sm text-slate-500">
              Side-by-side decision matrix comparing dedicated recovery dispatches against piggybacking.
            </p>
          </div>
        </div>
      </div>

      {misplacedShipments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm">
          <ShieldCheck className="h-10 w-10 text-emerald-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-slate-900">All Shipments On Track</h3>
          <p className="text-sm text-slate-500 mt-1">There are currently no misplaced shipments requiring planner evaluation.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Shipment Selector Dropdown */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <label className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <span>Select Misplaced Shipment:</span>
              <select
                value={selectedShipmentId}
                onChange={(e) => setSelectedShipmentId(Number(e.target.value))}
                className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {misplacedShipments.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.tracking_number} — {s.priority} Priority ({s.weight_kg}kg)
                  </option>
                ))}
              </select>
            </label>

            {currentShipment && (
              <div className="text-xs text-slate-600 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200">
                Location: <strong>{currentShipment.current_hub?.name || 'St. Louis Depot'}</strong> &rarr; Destination:{' '}
                <strong>{currentShipment.destination_hub?.name || 'Chicago Hub'}</strong>
              </div>
            )}
          </div>

          {/* Side-by-Side Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Option A: Dedicated Recovery Vehicle (Traditional) */}
            <div className="bg-white rounded-2xl p-6 border-2 border-slate-200 shadow-sm flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-slate-200 text-slate-700 text-[11px] font-bold px-3 py-1 rounded-bl-xl">
                Traditional Method
              </div>

              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="p-2 bg-slate-100 text-slate-700 rounded-lg">
                    <Truck className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Dedicated Recovery Truck</h3>
                    <p className="text-xs text-slate-500">Dispatch solo vehicle for special pickup & delivery</p>
                  </div>
                </div>

                <div className="space-y-4 my-6">
                  {/* Financial Cost */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-xs text-slate-500 mb-0.5">Estimated Cost</div>
                    <div className="text-2xl font-extrabold text-slate-900">${dedicatedCost.toFixed(2)}</div>
                    <div className="text-[11px] text-slate-500 mt-1">Includes driver wage, fuel & round-trip deadheading</div>
                  </div>

                  {/* CO2 Footprint */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-xs text-slate-500 mb-0.5">Carbon Emissions</div>
                    <div className="text-2xl font-extrabold text-rose-600">{dedicatedCO2.toFixed(1)} kg CO2</div>
                    <div className="text-[11px] text-slate-500 mt-1">Single-occupancy freight journey emissions</div>
                  </div>

                  {/* Capacity Efficiency */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-xs text-slate-500 mb-0.5">Capacity Utilization</div>
                    <div className="text-sm font-bold text-slate-800">
                      {currentShipment ? roundPercent((currentShipment.weight_kg / 3500) * 100) : 10}% (Highly Inefficient)
                    </div>
                    <div className="w-full bg-slate-200 h-2 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className="bg-rose-500 h-full"
                        style={{ width: `${currentShipment ? Math.min((currentShipment.weight_kg / 3500) * 100, 100) : 10}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                disabled
                className="w-full bg-slate-100 text-slate-400 font-semibold text-xs py-3 px-4 rounded-xl border border-slate-200 text-center cursor-not-allowed mt-4"
              >
                Dispatch Dedicated Truck (Coming soon)
              </button>
            </div>

            {/* Option B: Piggybacking on Active Route (ShipBridge AI) */}
            <div className="bg-white rounded-2xl p-6 border-2 border-emerald-500 shadow-md flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-emerald-600 text-white text-[11px] font-bold px-3 py-1 rounded-bl-xl shadow-sm">
                ShipBridge Recommended
              </div>

              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
                    <ShieldCheck className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Piggyback on Active Route</h3>
                    <p className="text-xs text-slate-500">Utilize spare capacity on existing passing truck</p>
                  </div>
                </div>

                <div className="space-y-4 my-6">
                  {/* Financial Cost */}
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200">
                    <div className="text-xs text-emerald-800 mb-0.5">Estimated Cost</div>
                    <div className="text-2xl font-extrabold text-emerald-700">${piggybackCost.toFixed(2)}</div>
                    <div className="text-[11px] text-emerald-700 font-semibold mt-1">
                      Saves ${(dedicatedCost - piggybackCost).toFixed(2)} compared to dedicated truck!
                    </div>
                  </div>

                  {/* CO2 Footprint */}
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200">
                    <div className="text-xs text-emerald-800 mb-0.5">Incremental Carbon Emissions</div>
                    <div className="text-2xl font-extrabold text-emerald-700">0.0 kg CO2</div>
                    <div className="text-[11px] text-emerald-700 font-semibold mt-1">
                      Prevents {dedicatedCO2.toFixed(1)} kg CO2 by eliminating a dedicated trip!
                    </div>
                  </div>

                  {/* Capacity Efficiency */}
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200">
                    <div className="text-xs text-emerald-800 mb-0.5">Vehicle Match & Capacity</div>
                    <div className="text-sm font-bold text-emerald-900">
                      {currentRec ? `${currentRec.vehicle_route.vehicle_code} (${currentRec.match_score}% Match)` : 'Route TRK-101'}
                    </div>
                    <div className="w-full bg-emerald-200 h-2 rounded-full mt-1.5 overflow-hidden">
                      <div className="bg-emerald-600 h-full" style={{ width: '85%' }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              {currentRec ? (
                <button
                  onClick={() => onAcceptRecommendation(currentRec)}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm py-3 px-4 rounded-xl shadow-md flex items-center justify-center gap-2 transition-all mt-4"
                >
                  <ShieldCheck className="h-5 w-5" />
                  Confirm & Execute Piggyback Plan
                </button>
              ) : (
                <button
                  disabled
                  className="w-full bg-slate-100 text-slate-400 font-semibold text-xs py-3 px-4 rounded-xl border border-slate-200 text-center cursor-not-allowed mt-4"
                >
                  No Piggyback Route Available for this Shipment
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function roundPercent(val: number): number {
  return Math.min(100, Math.max(1, Math.round(val)));
}
