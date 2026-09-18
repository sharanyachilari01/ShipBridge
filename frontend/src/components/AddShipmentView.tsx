import React, { useState } from 'react';
import { Hub, Shipment } from '../types';
import { createShipment } from '../api';
import { PlusCircle, CheckCircle2, AlertTriangle, Package, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';

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
  const generateTrackingNumber = () => `SB-IND-SH${Math.floor(100 + Math.random() * 900)}`;

  const [trackingNumber, setTrackingNumber] = useState<string>(generateTrackingNumber());
  const [originHubId, setOriginHubId] = useState<number>(hubs[0]?.id || 1);
  const [destinationHubId, setDestinationHubId] = useState<number>(hubs[1]?.id || 2);
  const [currentHubId, setCurrentHubId] = useState<number>(hubs[0]?.id || 1);
  const [weightKg, setWeightKg] = useState<number>(350);
  const [volumeM3, setVolumeM3] = useState<number>(2.2);
  const [priority, setPriority] = useState<string>('HIGH');
  const [notes, setNotes] = useState<string>('Standard logistics dispatch.');

  // Default deadlines
  const now = new Date();
  const defaultPickup = new Date(now.getTime() + 3 * 3600 * 1000).toISOString().slice(0, 16);
  const defaultDelivery = new Date(now.getTime() + 36 * 3600 * 1000).toISOString().slice(0, 16);
  
  const [pickupDeadline, setPickupDeadline] = useState<string>(defaultPickup);
  const [deliveryDeadline, setDeliveryDeadline] = useState<string>(defaultDelivery);

  // Demo controls state
  const [showDemoControls, setShowDemoControls] = useState<boolean>(false);
  const [simulateMisplaced, setSimulateMisplaced] = useState<boolean>(false); // Default OFF

  // Validation & Submission state
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [createdResult, setCreatedResult] = useState<Shipment | null>(null);

  const validateForm = (): string | null => {
    if (!trackingNumber.trim()) {
      return 'Tracking number is required.';
    }
    if (originHubId === destinationHubId) {
      return 'Origin hub and final destination hub cannot be the same.';
    }
    if (weightKg <= 0) {
      return 'Shipment weight must be greater than 0 kg.';
    }
    if (volumeM3 <= 0) {
      return 'Shipment volume must be greater than 0 m³.';
    }
    if (pickupDeadline && deliveryDeadline && new Date(deliveryDeadline) <= new Date(pickupDeadline)) {
      return 'Delivery deadline must be later than the pickup deadline.';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const error = validateForm();
    if (error) {
      setValidationError(error);
      return;
    }

    setSubmitting(true);
    setCreatedResult(null);

    try {
      const newShipment = await createShipment({
        tracking_number: trackingNumber.trim(),
        origin_hub_id: originHubId,
        destination_hub_id: destinationHubId,
        current_hub_id: currentHubId,
        weight_kg: weightKg,
        volume_m3: volumeM3,
        priority: priority,
        pickup_deadline: pickupDeadline ? new Date(pickupDeadline).toISOString() : undefined,
        delivery_deadline: deliveryDeadline ? new Date(deliveryDeadline).toISOString() : undefined,
        notes: notes,
        simulate_misplaced: simulateMisplaced,
      });

      setCreatedResult(newShipment);
      onShipmentCreated(newShipment);

      // Reset form with new tracking number
      setTrackingNumber(generateTrackingNumber());
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to register shipment. Check backend connectivity.';
      setValidationError(typeof msg === 'string' ? msg : JSON.stringify(msg));
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
              Dispatch freight across the India logistics network with automatic tracking & route monitoring.
            </p>
          </div>
        </div>
      </div>

      {/* Validation Error Alert */}
      {validationError && (
        <div className="bg-rose-50 border border-rose-300 rounded-2xl p-4 shadow-sm text-rose-900 flex items-start gap-3 animate-in fade-in">
          <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-bold text-xs uppercase tracking-wider text-rose-700">Form Validation Error</h4>
            <p className="text-sm mt-0.5 font-medium">{validationError}</p>
          </div>
        </div>
      )}

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
                Tracking Number: <strong className="font-mono">{createdResult.tracking_number}</strong> | Status:{' '}
                <strong className={createdResult.status === 'MISPLACED' ? 'text-rose-700 font-bold' : 'text-emerald-700 font-bold'}>
                  {createdResult.status}
                </strong>
              </p>
              <div className="mt-3 flex items-center gap-3">
                {createdResult.status === 'MISPLACED' ? (
                  <button
                    onClick={() => onSelectTab('queue')}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 shadow-sm transition-all"
                  >
                    View Recovery Options in Queue <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                ) : (
                  <button
                    onClick={() => onSelectTab('map')}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 shadow-sm transition-all"
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
              Tracking Code
            </label>
            <input
              type="text"
              required
              value={trackingNumber}
              onChange={(e) => setTrackingNumber(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-mono text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="e.g. SB-IND-SH035"
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
                  {h.name} ({h.city})
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
                  {h.name} ({h.city})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Current Location Hub, Weight, Volume */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Current Hub Location
            </label>
            <select
              value={currentHubId}
              onChange={(e) => setCurrentHubId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {hubs.map((h) => (
                <option key={`curr-${h.id}`} value={h.id}>
                  {h.name} ({h.city})
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
              max="20000"
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

        {/* Pickup & Delivery Deadlines */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Expected Pickup Time
            </label>
            <input
              type="datetime-local"
              value={pickupDeadline}
              onChange={(e) => setPickupDeadline(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Final Delivery Deadline
            </label>
            <input
              type="datetime-local"
              value={deliveryDeadline}
              onChange={(e) => setDeliveryDeadline(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Dispatch Notes */}
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Dispatch Notes & Handling Instructions
          </label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 text-xs text-slate-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="Special instructions or cargo details..."
          />
        </div>

        {/* Collapsible Demo / Test Controls (Default Collapsed, Toggle Off) */}
        <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50">
          <button
            type="button"
            onClick={() => setShowDemoControls(!showDemoControls)}
            className="w-full px-4 py-3 flex items-center justify-between text-xs font-bold text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <span className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Demo / Test Misplacement Controls
            </span>
            {showDemoControls ? (
              <ChevronUp className="h-4 w-4 text-slate-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-slate-400" />
            )}
          </button>

          {showDemoControls && (
            <div className="p-4 border-t border-slate-200 bg-amber-50/50 space-y-3">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simulateMisplaced}
                  onChange={(e) => setSimulateMisplaced(e.target.checked)}
                  className="mt-0.5 h-4 w-4 text-rose-600 rounded border-slate-300 focus:ring-rose-500"
                />
                <div>
                  <span className="text-xs font-bold text-rose-900 flex items-center gap-1">
                    Simulate Misplacement Flag Immediately
                  </span>
                  <p className="text-xs text-slate-600 mt-0.5">
                    When checked for testing, this shipment will register in MISPLACED status, automatically generating Stage 2 piggyback options and Stage 3 recommendations.
                  </p>
                </div>
              </label>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm py-3 px-4 rounded-xl shadow-md flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          <Package className="h-5 w-5" />
          {submitting ? 'Registering Shipment...' : 'Register Shipment'}
        </button>
      </form>
    </div>
  );
};
