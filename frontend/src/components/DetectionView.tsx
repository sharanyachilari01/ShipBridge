import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Radio,
  CheckCircle2,
  Clock,
  MapPin,
  Truck,
  Activity,
  ArrowRight,
  Info,
  SlidersHorizontal,
  Navigation
} from 'lucide-react';
import { DemoShipmentAnalysis, ShipmentException } from '../types';
import { fetchDemoShipmentsAnalysis, fetchExceptions } from '../api';

interface DetectionViewProps {
  onSelectShipmentId?: (id: number) => void;
}

const createLocationIcon = (isMisplaced: boolean) => {
  return L.divIcon({
    className: 'custom-det-icon',
    html: `<div style="background-color: ${isMisplaced ? '#e11d48' : '#2563eb'}; color: white; border: 2px solid white; border-radius: 9999px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
            ${isMisplaced ? '⚠️' : '🚚'}
          </div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

export const DetectionView: React.FC<DetectionViewProps> = ({ onSelectShipmentId }) => {
  const [demoCases, setDemoCases] = useState<DemoShipmentAnalysis[]>([]);
  const [exceptions, setExceptions] = useState<ShipmentException[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('SH009');
  const [showTestBench, setShowTestBench] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<'timestamp' | 'severity' | 'score'>('timestamp');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [demoData, excData] = await Promise.all([
        fetchDemoShipmentsAnalysis(),
        fetchExceptions()
      ]);
      setDemoCases(demoData);
      setExceptions(excData);
    } catch (err) {
      console.error('Failed to load detection evidence:', err);
    } finally {
      setLoading(false);
    }
  };

  const activeCase = demoCases.find((c) => c.shipment_id === selectedCaseId || c.tracking_number === selectedCaseId) || demoCases[0];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'MISPLACED':
        return { label: 'MISPLACED', bg: 'bg-rose-100 text-rose-800 border-rose-300', icon: ShieldAlert, color: 'text-rose-600' };
      case 'SUSPICIOUS':
        return { label: 'SUSPICIOUS', bg: 'bg-amber-100 text-amber-800 border-amber-300', icon: AlertTriangle, color: 'text-amber-600' };
      case 'NORMAL_REROUTED':
        return { label: 'NORMAL_REROUTED', bg: 'bg-blue-100 text-blue-800 border-blue-300', icon: CheckCircle2, color: 'text-blue-600' };
      case 'DELAYED':
        return { label: 'DELAYED', bg: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: Clock, color: 'text-yellow-600' };
      case 'UNKNOWN_SIGNAL_MONITOR':
        return { label: 'UNKNOWN_SIGNAL', bg: 'bg-slate-200 text-slate-800 border-slate-300', icon: Radio, color: 'text-slate-600' };
      case 'NORMAL':
      default:
        return { label: 'NORMAL', bg: 'bg-emerald-100 text-emerald-800 border-emerald-300', icon: ShieldCheck, color: 'text-emerald-600' };
    }
  };

  const sortedExceptions = [...exceptions].sort((a, b) => {
    if (sortBy === 'severity') return b.severity.localeCompare(a.severity);
    if (sortBy === 'score') return b.confidence_score - a.confidence_score;
    return new Date(b.detected_timestamp).getTime() - new Date(a.detected_timestamp).getTime();
  });

  if (loading || !activeCase) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)] text-slate-500 font-medium">
        <Activity className="h-8 w-8 animate-spin text-blue-600 mb-3" />
        <p className="text-slate-700">Analyzing Telemetry & Evidence Data...</p>
      </div>
    );
  }

  const isMisplaced = activeCase.current_status === 'MISPLACED';

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-2 bg-blue-100 text-blue-600 rounded-xl">
              <ShieldAlert className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Detection Evidence Audit</h1>
              <p className="text-xs text-slate-500">
                Audit evidence-based misplacement alerts, trajectory anomalies, and 7 false-positive safeguards.
              </p>
            </div>
          </div>
        </div>

        {/* Demo Controls Toggle */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700">
            <SlidersHorizontal className="h-3.5 w-3.5 text-slate-500" />
            <span>Demo/Test Data Bench</span>
            <input
              type="checkbox"
              checked={showTestBench}
              onChange={(e) => setShowTestBench(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-8 h-4 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600 relative"></div>
          </label>
        </div>
      </div>

      {/* Demo Test Bench Accordion (Visible only when toggle ON) */}
      {showTestBench && (
        <div className="bg-slate-900 text-white rounded-2xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-slate-300 border-b border-slate-800 pb-2">
            <span className="flex items-center gap-1.5 text-blue-400">
              <Activity className="h-4 w-4" /> Controlled Test Scenarios (SH001 through SH010)
            </span>
            <span className="text-slate-500">Demo Mode Active</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 md:grid-cols-10 gap-2">
            {demoCases.map((c) => {
              const isSelected = c.shipment_id === selectedCaseId;
              const badge = getStatusBadge(c.current_status);
              return (
                <button
                  key={c.shipment_id}
                  onClick={() => setSelectedCaseId(c.shipment_id)}
                  className={`p-2 rounded-xl border text-left transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-600/30 text-white shadow-md'
                      : 'border-slate-800 bg-slate-800/80 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  <span className="font-mono text-xs font-bold block">{c.shipment_id}</span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded mt-1 inline-block ${badge.bg}`}>
                    {c.current_status === 'UNKNOWN_SIGNAL_MONITOR' ? 'UNKNOWN' : c.current_status}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Evidence Layout: Exceptions List & Evidence Detail Map */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Exceptions Log Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-rose-500" />
              Shipment Exception Logs ({exceptions.length})
            </h3>

            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-[11px]">
              <span className="text-slate-500 font-medium ml-1">Sort:</span>
              <button
                onClick={() => setSortBy('timestamp')}
                className={`px-2 py-0.5 rounded font-semibold ${sortBy === 'timestamp' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'}`}
              >
                Time
              </button>
              <button
                onClick={() => setSortBy('severity')}
                className={`px-2 py-0.5 rounded font-semibold ${sortBy === 'severity' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'}`}
              >
                Severity
              </button>
            </div>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
            {sortedExceptions.map((exc) => {
              const isSelected = selectedCaseId === exc.tracking_number || selectedCaseId === `SH${exc.shipment_id.toString().padStart(3, '0')}`;
              return (
                <div
                  key={`exc-card-${exc.exception_id}`}
                  onClick={() => setSelectedCaseId(`SH${exc.shipment_id.toString().padStart(3, '0')}`)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-50 border-blue-500 shadow-sm'
                      : 'bg-slate-50/50 border-slate-200 hover:bg-slate-100/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-extrabold text-slate-900">
                      {exc.tracking_number || `SB-IND-SH${exc.shipment_id.toString().padStart(3, '0')}`}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${exc.severity === 'HIGH' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-800'}`}>
                      {exc.severity} SEVERITY
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 font-medium mt-1">
                    {exc.exception_type}
                  </p>

                  <p className="text-[11px] text-slate-500 mt-0.5 truncate" title={exc.exception_details || ''}>
                    {exc.exception_details || 'Deviation detected'}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2 pt-1.5 border-t border-slate-200/60">
                    <span>Confidence: <strong className="text-slate-700">{(exc.confidence_score * 100).toFixed(0)}%</strong></span>
                    <span>{new Date(exc.detected_timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Evidence & Compact Map */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Evidence Card */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-xl font-bold text-slate-900">{activeCase.tracking_number}</h3>
                  <span className="font-mono text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">
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
                  <div className={`flex items-center space-x-2 px-4 py-2 rounded-xl border font-bold text-xs ${badge.bg}`}>
                    <Icon className="h-4 w-4" />
                    <span>{badge.label}</span>
                  </div>
                );
              })()}
            </div>

            {/* Compact Evidence Corridor Map */}
            <div className="w-full h-56 rounded-xl overflow-hidden border border-slate-200 relative">
              <MapContainer
                center={[activeCase.current_lat || 20.0, activeCase.current_lng || 78.0]}
                zoom={6}
                scrollWheelZoom={false}
                style={{ width: '100%', height: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <Marker
                  position={[activeCase.current_lat, activeCase.current_lng]}
                  icon={createLocationIcon(isMisplaced)}
                >
                  <Popup>
                    <div className="text-xs font-bold text-slate-900 p-1">
                      {activeCase.tracking_number}<br />
                      Status: {activeCase.current_status}
                    </div>
                  </Popup>
                </Marker>
              </MapContainer>
            </div>

            {/* Explanation Callout */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-start space-x-3">
                <Info className="h-5 w-5 text-blue-600 mt-0.5 shrink-0" />
                <div>
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">
                    Detection Rationale & Evidence Summary
                  </h4>
                  <p className="text-xs text-slate-800 leading-relaxed font-medium">
                    {activeCase.explanation}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-2">
                    Primary Cause Code: <span className="font-mono font-bold text-slate-800">{activeCase.primary_cause}</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] font-semibold text-slate-500 block">Misplacement Score</span>
                <span className="text-xl font-bold text-slate-900">{activeCase.misplacement_score.toFixed(2)}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">Threshold: 0.65</span>
              </div>

              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] font-semibold text-slate-500 block">Corridor Deviation</span>
                <span className="text-xl font-bold text-slate-900">
                  {activeCase.distance_to_nearest_valid_route_km.toFixed(1)} km
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">Max allowed: 15.0 km</span>
              </div>

              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] font-semibold text-slate-500 block">Heading Difference</span>
                <span className="text-xl font-bold text-slate-900">
                  {activeCase.heading_difference_deg.toFixed(1)}°
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">Vector vs Route</span>
              </div>

              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                <span className="text-[10px] font-semibold text-slate-500 block">Persistence</span>
                <span className={`text-lg font-bold ${activeCase.persistent_anomaly ? 'text-rose-600' : 'text-slate-800'}`}>
                  {activeCase.persistent_anomaly ? 'PERSISTENT' : 'TRANSIENT'}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  {activeCase.telemetry_points_count} points checked
                </span>
              </div>
            </div>

            {/* Action button ONLY for MISPLACED shipments */}
            {isMisplaced && (
              <div className="pt-2">
                <button
                  onClick={() => onSelectShipmentId?.(activeCase.id)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs py-3 px-4 rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all"
                >
                  <Navigation className="h-4 w-4" />
                  View Piggyback Recovery Options for {activeCase.tracking_number} &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
