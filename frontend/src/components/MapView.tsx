import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Hub, Shipment, VehicleRoute, PiggybackRecommendation, AtRiskAlert, Stage2PiggybackOption } from '../types';
import { fetchAtRiskAlerts, fetchRecoveryOptions } from '../api';
import {
  AlertTriangle,
  CheckCircle2,
  Truck,
  ShieldCheck,
  ArrowRight,
  Clock,
  Building2,
  Info,
  Search,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Plus,
  Minus,
  Navigation,
  MapPin,
  CircleDot,
  Flag,
  Sparkles,
  SlidersHorizontal,
  Layers,
  Eye,
  EyeOff
} from 'lucide-react';

interface MapViewProps {
  hubs: Hub[];
  shipments: Shipment[];
  routes: VehicleRoute[];
  recommendations: PiggybackRecommendation[];
  selectedShipmentId?: number | null;
  onSelectShipmentId?: (id: number | null) => void;
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
  onSelectTab: (tab: 'queue' | 'planner') => void;
}

// Map Helper Component for Leaflet interactions
function MapController({
  selectedShipment,
  panTrigger,
  zoomTrigger
}: {
  selectedShipment: Shipment | null;
  panTrigger: { dx: number; dy: number; timestamp: number } | null;
  zoomTrigger: { delta: number; timestamp: number } | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedShipment && selectedShipment.current_lat && selectedShipment.current_lng) {
      map.flyTo([selectedShipment.current_lat, selectedShipment.current_lng], 7, { duration: 1.0 });
    }
  }, [selectedShipment, map]);

  useEffect(() => {
    if (panTrigger) {
      map.panBy([panTrigger.dx, panTrigger.dy], { animate: true, duration: 0.3 });
    }
  }, [panTrigger, map]);

  useEffect(() => {
    if (zoomTrigger) {
      if (zoomTrigger.delta > 0) map.zoomIn();
      else map.zoomOut();
    }
  }, [zoomTrigger, map]);

  return null;
}

// Leaflet Icons
const createSubtleHubIcon = (code: string) => {
  return L.divIcon({
    className: 'custom-hub-icon',
    html: `<div style="background-color: #1e293b; color: #94a3b8; border: 1px solid #475569; border-radius: 6px; padding: 1px 4px; font-size: 9px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2); white-space: nowrap;">
            📍 ${code}
          </div>`,
    iconSize: [55, 20],
    iconAnchor: [27, 10],
  });
};

const createTruckIcon = (code: string, isDelayed: boolean = false) => {
  const color = isDelayed ? '#d97706' : '#2563eb';
  return L.divIcon({
    className: 'custom-truck-icon',
    html: `<div style="background-color: ${color}; color: white; border: 2px solid white; border-radius: 8px; padding: 2px 6px; font-size: 10px; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 3px;">
            🚚 <span>${code}</span>
          </div>`,
    iconSize: [60, 24],
    iconAnchor: [30, 12],
  });
};

const createMisplacedIcon = () => {
  return L.divIcon({
    className: 'custom-misplaced-icon',
    html: `<div style="background-color: #e11d48; color: white; border: 2px solid white; border-radius: 9999px; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; box-shadow: 0 4px 12px rgba(225,29,72,0.6);">
            ⚠️
          </div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
};

const createAtRiskIcon = () => {
  return L.divIcon({
    className: 'custom-atrisk-icon',
    html: `<div style="background-color: #f59e0b; color: white; border: 2px solid white; border-radius: 9999px; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; box-shadow: 0 4px 10px rgba(245,158,11,0.6);">
            ⚡
          </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
};

const createCandidateVehicleIcon = (code: string, isFeasible: boolean, reason?: string) => {
  const bg = isFeasible ? '#059669' : '#d97706';
  const icon = isFeasible ? '✅' : '⚠️';
  return L.divIcon({
    className: 'custom-candidate-icon',
    html: `<div title="${reason || (isFeasible ? 'Feasible Candidate Vehicle' : 'Rejected Candidate')}" style="background-color: ${bg}; color: white; border: 2px solid white; border-radius: 8px; padding: 2px 6px; font-size: 10px; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.4); display: flex; align-items: center; gap: 3px;">
            ${icon} <span>${code}</span>
          </div>`,
    iconSize: [65, 24],
    iconAnchor: [32, 12],
  });
};

const createOriginIcon = () => {
  return L.divIcon({
    className: 'custom-origin-icon',
    html: `<div style="background-color: white; border: 3px solid #2563eb; border-radius: 9999px; width: 18px; height: 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
};

const createDestinationIcon = () => {
  return L.divIcon({
    className: 'custom-dest-icon',
    html: `<div style="background-color: #059669; color: white; border: 2px solid white; border-radius: 8px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; box-shadow: 0 3px 6px rgba(5,150,105,0.5);">🏁</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

export const MapView: React.FC<MapViewProps> = ({
  hubs,
  shipments,
  routes,
  recommendations,
  selectedShipmentId,
  onSelectShipmentId,
  onAcceptRecommendation,
  onSelectTab,
}) => {
  const [filterTab, setFilterTab] = useState<'ALL' | 'MISPLACED' | 'AT_RISK' | 'HIGH' | 'DELAYED'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [panelOpen, setPanelOpen] = useState<boolean>(true);
  const [showLayerControl, setShowLayerControl] = useState<boolean>(false);
  const [panTrigger, setPanTrigger] = useState<{ dx: number; dy: number; timestamp: number } | null>(null);
  const [zoomTrigger, setZoomTrigger] = useState<{ delta: number; timestamp: number } | null>(null);

  // Early At-Risk Alerts & Candidate Opportunities
  const [atRiskAlerts, setAtRiskAlerts] = useState<AtRiskAlert[]>([]);
  const [candidateOptions, setCandidateOptions] = useState<Stage2PiggybackOption[]>([]);

  // 7 Toggleable Layer Controls
  const [layers, setLayers] = useState({
    availableVehicles: true,
    delayedVehicles: true,
    limitedCapacityVehicles: true,
    transferHubs: true,
    allShipments: true,
    atRiskShipments: true,
    misplacedShipments: true,
  });

  useEffect(() => {
    loadAtRiskAlerts();
  }, []);

  const loadAtRiskAlerts = async () => {
    try {
      const alerts = await fetchAtRiskAlerts();
      setAtRiskAlerts(alerts);
    } catch (err) {
      console.error('Failed to load at-risk alerts:', err);
    }
  };

  const selectedShipment = shipments.find((s) => s.id === selectedShipmentId) || null;

  // Load candidate opportunities for Explain Search Mode
  useEffect(() => {
    if (selectedShipment && selectedShipment.status === 'MISPLACED') {
      fetchRecoveryOptions(selectedShipment.id)
        .then((res) => setCandidateOptions(res.opportunities || []))
        .catch(() => setCandidateOptions([]));
    } else {
      setCandidateOptions([]);
    }
  }, [selectedShipmentId]);

  const atRiskShipmentIds = new Set(atRiskAlerts.map((a) => a.shipment_id));

  // Filter shipments for panel list
  const filteredShipments = shipments.filter((s) => {
    const matchesSearch =
      s.tracking_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.origin_hub?.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.destination_hub?.name || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (filterTab === 'ALL') return true;
    if (filterTab === 'MISPLACED') return s.status === 'MISPLACED';
    if (filterTab === 'AT_RISK') return atRiskShipmentIds.has(s.id);
    if (filterTab === 'HIGH') return s.priority === 'HIGH' || s.priority === 'CRITICAL';
    if (filterTab === 'DELAYED') return s.status === 'DELAYED';
    return true;
  });

  const handlePan = (dx: number, dy: number) => {
    setPanTrigger({ dx, dy, timestamp: Date.now() });
  };

  const handleZoom = (delta: number) => {
    setZoomTrigger({ delta, timestamp: Date.now() });
  };

  const toggleLayer = (layerKey: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

  const selectedRec = selectedShipment ? recommendations.find((r) => r.shipment.id === selectedShipment.id) : null;

  return (
    <div className="relative w-full h-[calc(100vh-7rem)] bg-slate-900 flex overflow-hidden">
      {/* Collapsible Left Control Panel */}
      <div
        className={`absolute top-0 bottom-0 left-0 z-[600] bg-white border-r border-slate-200 shadow-xl transition-all duration-300 flex flex-col ${
          panelOpen ? 'w-80 md:w-96' : 'w-0 overflow-hidden border-none'
        }`}
      >
        <div className="p-4 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base flex items-center gap-2 text-white">
              <Navigation className="h-4 w-4 text-blue-400" />
              Network Control Tower
            </h2>
            <p className="text-xs text-slate-400">Live Logistics & Explainable Piggyback Search</p>
          </div>
          <button
            onClick={() => setPanelOpen(false)}
            className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
            title="Collapse panel"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        </div>

        {/* Search Bar & Filters */}
        <div className="p-3 border-b border-slate-100 bg-slate-50 space-y-2">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search tracking ID or hub..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px]">
            {(['ALL', 'MISPLACED', 'AT_RISK', 'HIGH', 'DELAYED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterTab(tab)}
                className={`px-2 py-0.5 rounded-md font-bold transition-all whitespace-nowrap ${
                  filterTab === tab
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {tab === 'ALL'
                  ? `All (${shipments.length})`
                  : tab === 'MISPLACED'
                  ? `Misplaced (${shipments.filter((s) => s.status === 'MISPLACED').length})`
                  : tab === 'AT_RISK'
                  ? `At-Risk (${atRiskAlerts.length})`
                  : tab === 'HIGH'
                  ? `High Priority`
                  : `Delayed`}
              </button>
            ))}
          </div>
        </div>

        {/* Shipment Panel List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
          {filteredShipments.map((shp) => {
            const isSelected = selectedShipment?.id === shp.id;
            const isAtRisk = atRiskShipmentIds.has(shp.id);
            return (
              <div
                key={`panel-shp-${shp.id}`}
                onClick={() => onSelectShipmentId?.(shp.id)}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-blue-50 border-blue-500 shadow-sm'
                    : 'bg-white border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-extrabold text-slate-900">
                    {shp.tracking_number}
                  </span>
                  <div className="flex items-center gap-1">
                    {isAtRisk && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                        AT RISK
                      </span>
                    )}
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        shp.status === 'MISPLACED'
                          ? 'bg-rose-100 text-rose-700 border border-rose-300'
                          : shp.status === 'DELAYED'
                          ? 'bg-amber-100 text-amber-800 border border-amber-300'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {shp.status}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-slate-600 mt-1 flex items-center justify-between">
                  <span>
                    {shp.origin_hub?.city || 'Origin'} &rarr; {shp.destination_hub?.city || 'Destination'}
                  </span>
                  <span className="font-semibold text-slate-800">{shp.weight_kg}kg</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Open Panel Toggle Button */}
      {!panelOpen && (
        <button
          onClick={() => setPanelOpen(true)}
          className="absolute top-4 left-4 z-[500] bg-slate-900 text-white p-2.5 rounded-xl shadow-lg border border-slate-700 hover:bg-slate-800 transition-all flex items-center gap-1.5 text-xs font-bold"
        >
          <ChevronRight className="h-4 w-4" />
          <span>Control Panel</span>
        </button>
      )}

      {/* Top Right: 7 Layer Control Toggle Panel */}
      <div className="absolute top-4 right-4 z-[500] flex flex-col items-end gap-2">
        <button
          onClick={() => setShowLayerControl(!showLayerControl)}
          className="bg-slate-900/90 text-white p-2.5 rounded-xl shadow-xl border border-slate-700 flex items-center gap-2 text-xs font-bold hover:bg-slate-800 transition-all"
        >
          <Layers className="h-4 w-4 text-blue-400" />
          <span>Map Layers (7)</span>
        </button>

        {showLayerControl && (
          <div className="bg-slate-900/95 text-white p-3 rounded-2xl shadow-2xl border border-slate-700 text-xs w-64 space-y-2 animate-in fade-in">
            <div className="font-bold text-slate-200 border-b border-slate-800 pb-1.5 flex items-center justify-between">
              <span>Toggleable Map Layers</span>
              <span className="text-[10px] text-blue-400">Live Filters</span>
            </div>

            <div className="space-y-1.5 text-[11px]">
              {([
                ['availableVehicles', 'Available Vehicles'],
                ['delayedVehicles', 'Delayed Vehicles'],
                ['limitedCapacityVehicles', 'Limited Capacity Trucks'],
                ['transferHubs', 'Transfer Hubs'],
                ['allShipments', 'All Active Shipments'],
                ['atRiskShipments', 'At-Risk Shipments'],
                ['misplacedShipments', 'Misplaced Shipments'],
              ] as const).map(([key, label]) => (
                <label key={key} className="flex items-center justify-between cursor-pointer hover:bg-slate-800/60 p-1 rounded">
                  <span className="text-slate-300 font-medium">{label}</span>
                  <input
                    type="checkbox"
                    checked={layers[key]}
                    onChange={() => toggleLayer(key)}
                    className="rounded border-slate-700 text-blue-500 focus:ring-blue-500 bg-slate-800"
                  />
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Map Control Buttons (Pan & Zoom) */}
        <div className="bg-slate-900/90 p-2 rounded-2xl shadow-xl border border-slate-700 flex flex-col items-center gap-1">
          <button onClick={() => handleZoom(1)} className="p-1.5 text-slate-300 hover:text-white" title="Zoom In">
            <Plus className="h-4 w-4" />
          </button>
          <button onClick={() => handleZoom(-1)} className="p-1.5 text-slate-300 hover:text-white" title="Zoom Out">
            <Minus className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Leaflet Map */}
      <div className="w-full flex-1">
        <MapContainer
          center={[20.5937, 78.9629]}
          zoom={5}
          scrollWheelZoom={false}
          style={{ width: '100%', height: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapController
            selectedShipment={selectedShipment}
            panTrigger={panTrigger}
            zoomTrigger={zoomTrigger}
          />

          {/* Transfer Hub Markers */}
          {layers.transferHubs &&
            hubs.map((hub) => (
              <Marker key={`hub-${hub.id}`} position={[hub.latitude, hub.longitude]} icon={createSubtleHubIcon(hub.code)}>
                <Popup>
                  <div className="p-1 max-w-xs">
                    <div className="font-bold text-slate-900 text-xs flex items-center gap-1">
                      <Building2 className="h-3.5 w-3.5 text-blue-600" />
                      {hub.name}
                    </div>
                    <div className="text-[11px] text-slate-600 mt-1">{hub.city}, {hub.state}</div>
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* Active Fleet Vehicle Markers */}
          {routes.map((route) => {
            const isDelayed = route.status === 'DELAYED';
            if (isDelayed && !layers.delayedVehicles) return null;
            if (!isDelayed && !layers.availableVehicles) return null;

            const firstWp = route.waypoints?.[0];
            if (!firstWp) return null;

            return (
              <Marker
                key={`route-v-${route.id}`}
                position={[firstWp.lat, firstWp.lng]}
                icon={createTruckIcon(route.vehicle_code, isDelayed)}
              >
                <Popup>
                  <div className="p-1 text-xs">
                    <div className="font-bold text-slate-900">{route.vehicle_code}</div>
                    <div className="text-slate-600">{route.vehicle_type}</div>
                    <div className="text-[11px] text-slate-500 mt-1">Cap: {route.spare_capacity_kg}kg spare</div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Shipment Markers (Normal, At-Risk, Misplaced) */}
          {shipments.map((shp) => {
            const isMisplaced = shp.status === 'MISPLACED';
            const isAtRisk = atRiskShipmentIds.has(shp.id);

            if (isMisplaced && !layers.misplacedShipments) return null;
            if (isAtRisk && !layers.atRiskShipments) return null;
            if (!isMisplaced && !isAtRisk && !layers.allShipments) return null;

            const lat = shp.current_lat || shp.origin_hub?.latitude || 20.0;
            const lng = shp.current_lng || shp.origin_hub?.longitude || 78.0;

            const icon = isMisplaced
              ? createMisplacedIcon()
              : isAtRisk
              ? createAtRiskIcon()
              : createTruckIcon(shp.tracking_number);

            return (
              <Marker
                key={`shipment-m-${shp.id}`}
                position={[lat, lng]}
                icon={icon}
                eventHandlers={{
                  click: () => onSelectShipmentId?.(shp.id),
                }}
              >
                <Popup>
                  <div className="p-1 max-w-xs">
                    <div className="font-mono text-xs font-bold text-slate-900">{shp.tracking_number}</div>
                    <div className="text-[11px] text-slate-600 mt-0.5">
                      Status: <strong className={isMisplaced ? 'text-rose-600' : isAtRisk ? 'text-amber-600' : 'text-emerald-600'}>{shp.status}</strong>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Explain Search Mode: Candidate Recovery Vehicles & Multi-Hop Route Vectors */}
          {selectedShipment && candidateOptions.length > 0 && (
            <React.Fragment key={`candidate-search-${selectedShipment.id}`}>
              {candidateOptions.map((opt) => {
                const isFeasible = opt.is_feasible;
                const reason = opt.rejection_reasons?.join(' | ') || opt.explanation;

                // Pickup location
                const pickupHub = hubs.find((h) => h.id === opt.pickup_hub_id);
                if (!pickupHub) return null;

                return (
                  <React.Fragment key={`candidate-opt-${opt.candidate_id}`}>
                    <Marker
                      position={[pickupHub.latitude, pickupHub.longitude]}
                      icon={createCandidateVehicleIcon(opt.vehicle_code, isFeasible, reason)}
                    >
                      <Tooltip permanent={false} direction="top">
                        <div className="text-xs p-1">
                          <strong className={isFeasible ? 'text-emerald-600' : 'text-amber-600'}>
                            {opt.vehicle_code} — {isFeasible ? 'FEASIBLE' : 'REJECTED'}
                          </strong>
                          <p className="text-[11px] text-slate-700 mt-0.5">{reason}</p>
                        </div>
                      </Tooltip>
                    </Marker>

                    {/* Multi-hop Route Vector Line Styling */}
                    {opt.route_geometry && opt.route_geometry.length > 1 && (
                      <Polyline
                        positions={opt.route_geometry.map((g) => [g.lat, g.lng])}
                        pathOptions={{
                          color: opt.number_of_transfers === 0 ? '#059669' : opt.number_of_transfers === 1 ? '#06b6d4' : '#6366f1',
                          weight: 4,
                          dashArray: opt.number_of_transfers === 1 ? '6,6' : opt.number_of_transfers === 2 ? '2,4' : undefined,
                          opacity: 0.85,
                        }}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </React.Fragment>
          )}

          {/* Selected Journey Line (Origin -> Current -> Dest) */}
          {selectedShipment && selectedShipment.origin_hub && selectedShipment.destination_hub && (
            <React.Fragment key={`selected-journey-${selectedShipment.id}`}>
              <Marker position={[selectedShipment.origin_hub.latitude, selectedShipment.origin_hub.longitude]} icon={createOriginIcon()} />
              <Marker position={[selectedShipment.destination_hub.latitude, selectedShipment.destination_hub.longitude]} icon={createDestinationIcon()} />
              <Polyline
                positions={[
                  [selectedShipment.origin_hub.latitude, selectedShipment.origin_hub.longitude],
                  [selectedShipment.current_lat || selectedShipment.origin_hub.latitude, selectedShipment.current_lng || selectedShipment.origin_hub.longitude],
                  [selectedShipment.destination_hub.latitude, selectedShipment.destination_hub.longitude],
                ]}
                pathOptions={{
                  color: selectedShipment.status === 'MISPLACED' ? '#e11d48' : '#2563eb',
                  weight: 4,
                  dashArray: selectedShipment.status === 'MISPLACED' ? '6,6' : undefined,
                }}
              />
            </React.Fragment>
          )}
        </MapContainer>
      </div>

      {/* Floating Selected Shipment Detail Card */}
      {selectedShipment && (
        <div className="absolute bottom-4 right-4 z-[600] w-96 max-w-full bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 transition-all space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-base font-extrabold text-slate-900">
                  {selectedShipment.tracking_number}
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${selectedShipment.status === 'MISPLACED' ? 'bg-rose-100 text-rose-700 border border-rose-300' : 'bg-emerald-100 text-emerald-800'}`}>
                  {selectedShipment.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedShipment.origin_hub?.name || 'Origin'} &rarr; {selectedShipment.destination_hub?.name || 'Destination'}
              </p>
            </div>
            <button onClick={() => onSelectShipmentId?.(null)} className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1">
              ✕
            </button>
          </div>

          {selectedRec ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs space-y-2">
              <div className="flex items-center justify-between font-bold text-emerald-900">
                <span className="flex items-center gap-1">
                  <Sparkles className="h-4 w-4 text-emerald-600" /> Recommended Piggyback
                </span>
                <span className="bg-emerald-600 text-white text-[10px] px-2 py-0.5 rounded-full">
                  Score {selectedRec.match_score}%
                </span>
              </div>
              <p className="text-emerald-800 leading-relaxed">{selectedRec.explanation}</p>
              <button
                onClick={() => onAcceptRecommendation(selectedRec)}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-lg shadow-sm flex items-center justify-center gap-1"
              >
                <ShieldCheck className="h-4 w-4" /> Approve Piggyback Recovery
              </button>
            </div>
          ) : selectedShipment.status === 'MISPLACED' ? (
            <button
              onClick={() => onSelectTab('planner')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs py-2 px-3 rounded-xl shadow-sm flex items-center justify-center gap-1"
            >
              <Navigation className="h-4 w-4" /> Open Recovery Planner
            </button>
          ) : (
            <div className="text-xs text-slate-500 bg-slate-50 p-2 rounded-lg text-center">
              Shipment is on-track along corridor.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
