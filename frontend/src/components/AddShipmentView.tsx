import React, { useState } from 'react';
import { Hub, Shipment } from '../types';
import { createShipment } from '../api';
import { PlusCircle, CheckCircle2, AlertTriangle, Package, ArrowRight } from 'lucide-react';

interface AddShipmentViewProps {
  hubs: Hub[];
  onShipmentCreated: (shipment: Shipment) => void;
  onSelectTab: (tab: 'map' | 'queue') => void;
}

export const AddShipmentView: React.FC<AddShipmentViewProps> = ({
  hubs,
  onShipmentCreated,
  onSelectTab,
}) => {
  const [trackingNumber, setTrackingNumber] = useState<string>(
    `SHP-${Math.floor(1000 + Math.random() * 9000)}-${['IL', 'IN', 'MO', 'OH'][Math.floor(Math.random() * 4)]}`
  );
  const [originHubId, setOriginHubId] = useState<number>(hubs[0]?.id || 1);
  const [destinationHubId, setDestinationHubId] = useState<number>(hubs[1]?.id || 2);
  const [currentHubId, setCurrentHubId] = useState<number>(hubs[2]?.id || 3);
  const [weightKg, setWeightKg] = useState<number>(240);
  const [volumeM3, setVolumeM3] = useState<number>(1.5);
  const [priority, setPriority] = useState<string>('HIGH');
  const [simulateMisplaced, setSimulateMisplaced] = useState<boolean>(true);
  const [notes, setNotes] = useState<string>('Dispatched from origin; misplaced at interchange sorting hub.');

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [createdResult, setCreatedResult] = useState<Shipment | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setCreatedResult(null);

    try {
      const newShipment = await createShipment({
        tracking_number: trackingNumber,
        origin_hub_id: originHubId,
        destination_hub_id: destinationHubId,
        current_hub_id: currentHubId,
        weight_kg: weightKg,
        volume_m3: volumeM3,
        priority: priority,
        notes: notes,
        simulate_misplaced: simulateMisplaced,
      });

      setCreatedResult(newShipment);
      onShipmentCreated(newShipment);

      // Generate next random tracking number for convenience
      setTrackingNumber(
        `SHP-${Math.floor(1000 + Math.random() * 9000)}-${['IL', 'IN', 'MO', 'OH'][Math.floor(Math.random() * 4)]}`
      );
    } catch (err) {
      alert('Failed to register shipment. Check backend status.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex items-center gap-3">
          <span className="p-2.5 bg-blue-100 text-blue-600 rounded-xl">
            <PlusCircle className="h-6 w-6" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Register New Shipment</h2>
            <p className="text-sm text-slate-500">
              Add a shipment to the ShipBridge network and optional test misplacement simulation.
            </p>
          </div>
        </div>
      </div>

      {/* Success Notification Banner */}
      {createdResult && (
        <div className="bg-emerald-50 border-2 border-emerald-300 rounded-2xl p-5 shadow-sm animate-in fade-in">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-bold text-emerald-900 text-base">
                Shipment Registered Successfully!
              </h3>
              <p className="text-xs text-emerald-800 mt-1">
                Tracking Number: <strong>{createdResult.tracking_number}</strong> | Status:{' '}
                <strong className={createdResult.status === 'MISPLACED' ? 'text-rose-700' : 'text-emerald-700'}>
                  {createdResult.status}
                </strong>
              </p>
              <div className="mt-3 flex items-center gap-3">
                {createdResult.status === 'MISPLACED' ? (
                  <button
                    onClick={() => onSelectTab('queue')}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 shadow-sm"
                  >
                    View Piggyback Options in Queue <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                ) : (
                  <button
                    onClick={() => onSelectTab('map')}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 shadow-sm"
                  >
                    View on Live Map <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Shipment Registration Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Tracking Number */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Tracking Number / Code
            </label>
            <input
              type="text"
              required
              value={trackingNumber}
              onChange={(e) => setTrackingNumber(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-mono text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Logistics Priority Level
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="NORMAL">NORMAL (Standard Freight)</option>
              <option value="HIGH">HIGH (Expedited Transit)</option>
              <option value="CRITICAL">CRITICAL (Cold-chain / Time-sensitive)</option>
            </select>
          </div>
        </div>

        {/* Origin & Destination Hubs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Origin Hub
            </label>
            <select
              value={originHubId}
              onChange={(e) => setOriginHubId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {hubs.map((h) => (
                <option key={`orig-${h.id}`} value={h.id}>
                  {h.name} ({h.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Final Destination Hub
            </label>
            <select
              value={destinationHubId}
              onChange={(e) => setDestinationHubId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {hubs.map((h) => (
                <option key={`dest-${h.id}`} value={h.id}>
                  {h.name} ({h.code})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Current Location Hub & Weight */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Current Location Hub
            </label>
            <select
              value={currentHubId}
              onChange={(e) => setCurrentHubId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {hubs.map((h) => (
                <option key={`curr-${h.id}`} value={h.id}>
                  {h.name} ({h.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Weight (kg)
            </label>
            <input
              type="number"
              required
              min="1"
              max="15000"
              value={weightKg}
              onChange={(e) => setWeightKg(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Volume (m³)
            </label>
            <input
              type="number"
              step="0.1"
              required
              min="0.1"
              max="50"
              value={volumeM3}
              onChange={(e) => setVolumeM3(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Misplacement Simulation Checkbox */}
        <div className="p-4 bg-rose-50 rounded-xl border border-rose-200">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={simulateMisplaced}
              onChange={(e) => setSimulateMisplaced(e.target.checked)}
              className="mt-0.5 h-4 w-4 text-rose-600 rounded border-slate-300 focus:ring-rose-500"
            />
            <div>
              <span className="text-xs font-bold text-rose-900 flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />
                Simulate Misplacement State Immediately
              </span>
              <p className="text-xs text-rose-800 mt-0.5">
                When checked, this shipment will be flagged as MISPLACED upon registration, generating piggyback recovery recommendations against active vehicle routes.
              </p>
            </div>
          </label>
        </div>

        {/* Notes / Rationale */}
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Dispatch Notes / Cargo Rationale
          </label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 text-xs text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="Additional handling instructions..."
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm py-3 px-4 rounded-xl shadow-md flex items-center justify-center gap-2 transition-all"
        >
          <Package className="h-5 w-5" />
          {submitting ? 'Registering Shipment...' : 'Register Shipment'}
        </button>
      </form>
    </div>
  );
};
