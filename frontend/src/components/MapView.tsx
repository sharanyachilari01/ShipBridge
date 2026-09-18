import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Hub, Shipment, VehicleRoute, PiggybackRecommendation } from '../types';
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
  SlidersHorizontal
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

// Subtle Hub Marker
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

// Truck / Current Location Marker
const createTruckIcon = (code: string) => {
  return L.divIcon({
    className: 'custom-truck-icon',
    html: `<div style="background-color: #2563eb; color: white; border: 2px solid white; border-radius: 8px; padding: 2px 6px; font-size: 10px; font-weight: bold; box-shadow: 0 4px 8px rgba(37,99,235,0.4); display: flex; align-items: center; gap: 3px;">
            🚚 <span>${code}</span>
          </div>`,
    iconSize: [60, 24],
    iconAnchor: [30, 12],
  });
};

// Misplaced Marker (RED Alert)
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

// Origin Marker (Outlined Blue Circle)
const createOriginIcon = () => {
  return L.divIcon({
    className: 'custom-origin-icon',
    html: `<div style="background-color: white; border: 3px solid #2563eb; border-radius: 9999px; width: 18px; height: 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
};

// Destination Marker (Flag Pin)
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
  const [filterTab, setFilterTab] = useState<'ALL' | 'MISPLACED' | 'HIGH' | 'DELAYED' | 'ON_TRACK'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [panelOpen, setPanelOpen] = useState<boolean>(true);
  const [panTrigger, setPanTrigger] = useState<{ dx: number; dy: number; timestamp: number } | null>(null);
  const [zoomTrigger, setZoomTrigger] = useState<{ delta: number; timestamp: number } | null>(null);

  // Geographic center of India
  const centerLat = 20.5937;
  const centerLng = 78.9629;
  const defaultZoom = 5;

  const selectedShipment = shipments.find((s) => s.id === selectedShipmentId) || null;

  // Filter shipments for panel list
  const filteredShipments = shipments.filter((s) => {
    const matchesSearch =
      s.tracking_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.origin_hub?.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.destination_hub?.name || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (filterTab === 'ALL') return true;
    if (filterTab === 'MISPLACED') return s.status === 'MISPLACED';
    if (filterTab === 'HIGH') return s.priority === 'HIGH' || s.priority === 'CRITICAL';
    if (filterTab === 'DELAYED') return s.status === 'DELAYED';
    if (filterTab === 'ON_TRACK') return s.status !== 'MISPLACED';
    return true;
  });

  const handlePan = (dx: number, dy: number) => {
    setPanTrigger({ dx, dy, timestamp: Date.now() });
  };

  const handleZoom = (delta: number) => {
    setZoomTrigger({ delta, timestamp: Date.now() });
  };

  const selectedRec = selectedShipment ? recommendations.find((r) => r.shipment.id === selectedShipment.id) : null;

  return (
    <div className="relative w-full h-[calc(100vh-7rem)] bg-slate-900 flex overflow-hidden">
      {/* Collapsible Left Shipment Panel */}
      <div
        className={`absolute top-0 bottom-0 left-0 z-[600] bg-white border-r border-slate-200 shadow-xl transition-all duration-300 flex flex-col ${
          panelOpen ? 'w-80 md:w-96' : 'w-0 overflow-hidden border-none'
        }`}
      >
        <div className="p-4 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base flex items-center gap-2 text-white">
              <Navigation className="h-4 w-4 text-blue-400" />
              Network Control Panel
            </h2>
            <p className="text-xs text-slate-400">Live Indian Cargo Fleet & Shipments</p>
          </div>
          <button
            onClick={() => setPanelOpen(false)}
            className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
            title="Collapse panel"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b border-slate-100 bg-slate-50">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search tracking ID or hub city..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 mt-2 overflow-x-auto pb-1 text-[11px]">
            {(['ALL', 'MISPLACED', 'HIGH', 'DELAYED', 'ON_TRACK'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterTab(tab)}
                className={`px-2.5 py-1 rounded-md font-semibold transition-all whitespace-nowrap ${
                  filterTab === tab
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {tab === 'ALL'
                  ? `All (${shipments.length})`
                  : tab === 'MISPLACED'
                  ? `Misplaced (${shipments.filter((s) => s.status === 'MISPLACED').length})`
                  : tab === 'HIGH'
                  ? `High Priority`
                  : tab === 'DELAYED'
                  ? `Delayed`
                  : `On-Track`}
              </button>
            ))}
          </div>
        </div>

        {/* Shipment List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
          {filteredShipments.map((shp) => {
            const isSelected = selectedShipment?.id === shp.id;
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

                <div className="text-xs text-slate-600 mt-1 flex items-center justify-between">
                  <span>
                    {shp.origin_hub?.city || 'Bengaluru'} &rarr; {shp.destination_hub?.city || 'Delhi'}
                  </span>
                  <span className="font-semibold text-slate-800">{shp.weight_kg}kg</span>
                </div>

                <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                  <span>Priority: <strong className="text-slate-700">{shp.priority}</strong></span>
                  {shp.status === 'MISPLACED' && (
                    <span className="text-rose-600 font-bold">Action Needed &rarr;</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Open Panel Button when collapsed */}
      {!panelOpen && (
        <button
          onClick={() => setPanelOpen(true)}
          className="absolute top-4 left-4 z-[500] bg-slate-900 text-white p-2.5 rounded-xl shadow-lg border border-slate-700 hover:bg-slate-800 transition-all flex items-center gap-1.5 text-xs font-bold"
        >
          <ChevronRight className="h-4 w-4" />
          <span>Shipment Panel</span>
        </button>
      )}

      {/* Visible Map Controls Pad (Pan Pad & Zoom Buttons) */}
      <div className="absolute top-4 right-4 z-[500] flex flex-col gap-2">
        {/* Navigation Pad */}
        <div className="bg-slate-900/90 backdrop-blur-md p-2 rounded-2xl shadow-xl border border-slate-700 flex flex-col items-center">
          <button
            onClick={() => handlePan(0, -150)}
            className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
            title="Pan Up"
          >
            <ChevronUp className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-1 my-1">
            <button
              onClick={() => handlePan(-150, 0)}
              className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
              title="Pan Left"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <button
              onClick={() => handlePan(150, 0)}
              className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
              title="Pan Right"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          <button
            onClick={() => handlePan(0, 150)}
            className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
            title="Pan Down"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="bg-slate-900/90 backdrop-blur-md p-1 rounded-xl shadow-xl border border-slate-700 flex flex-col items-center gap-1">
          <button
            onClick={() => handleZoom(1)}
            className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
            title="Zoom In"
          >
            <Plus className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleZoom(-1)}
            className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg"
            title="Zoom Out"
          >
            <Minus className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Map Legend Overlay (Bottom Left) */}
      <div className="absolute bottom-4 left-4 z-[500] bg-slate-900/90 text-white p-3 rounded-xl shadow-xl border border-slate-700 text-xs hidden sm:block max-w-xs">
        <div className="font-bold text-slate-200 mb-1.5 flex items-center gap-1">
          <Info className="h-3.5 w-3.5 text-blue-400" />
          Journey Legend
        </div>
        <div className="space-y-1 text-[11px] text-slate-300">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border-2 border-blue-500 bg-white" />
            <span>Origin Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs">🚚</span>
            <span>Current Cargo Location</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs">🏁</span>
            <span>Destination Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-blue-500" />
            <span>Active Journey Corridor</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-rose-500 border-t border-dashed border-rose-500" />
            <span>Misplaced Deviation</span>
          </div>
        </div>
      </div>

      {/* Main Leaflet Map */}
      <div className="w-full flex-1">
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={defaultZoom}
          scrollWheelZoom={false} // Disable mouse wheel zoom to prevent page scroll trapping
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

          {/* Hub Markers (Subtle Icons) */}
          {hubs.map((hub) => (
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

          {/* Current Shipment Location Markers */}
          {shipments.map((shp) => {
            const lat = shp.current_lat || shp.origin_hub?.latitude || 20.0;
            const lng = shp.current_lng || shp.origin_hub?.longitude || 78.0;

            const isSelected = selectedShipment?.id === shp.id;
            const isMisplaced = shp.status === 'MISPLACED';

            return (
              <Marker
                key={`shipment-marker-${shp.id}`}
                position={[lat, lng]}
                icon={isMisplaced ? createMisplacedIcon() : createTruckIcon(shp.tracking_number)}
                eventHandlers={{
                  click: () => onSelectShipmentId?.(shp.id),
                }}
              >
                <Popup>
                  <div className="p-1 max-w-xs">
                    <div className="font-mono text-xs font-bold text-slate-900">{shp.tracking_number}</div>
                    <div className="text-[11px] text-slate-600 mt-0.5">
                      Status: <strong className={isMisplaced ? 'text-rose-600' : 'text-emerald-600'}>{shp.status}</strong>
                    </div>
                    <div className="text-[11px] text-slate-600">Priority: {shp.priority} | {shp.weight_kg}kg</div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Selected Shipment Journey Visualization */}
          {selectedShipment && selectedShipment.origin_hub && selectedShipment.destination_hub && (
            <React.Fragment key={`selected-journey-${selectedShipment.id}`}>
              {/* Origin Marker */}
              <Marker
                position={[selectedShipment.origin_hub.latitude, selectedShipment.origin_hub.longitude]}
                icon={createOriginIcon()}
              />

              {/* Destination Marker */}
              <Marker
                position={[selectedShipment.destination_hub.latitude, selectedShipment.destination_hub.longitude]}
                icon={createDestinationIcon()}
              />

              {/* Planned Route Line (Origin -> Destination) */}
              <Polyline
                positions={[
                  [selectedShipment.origin_hub.latitude, selectedShipment.origin_hub.longitude],
                  [
                    selectedShipment.current_lat || selectedShipment.origin_hub.latitude,
                    selectedShipment.current_lng || selectedShipment.origin_hub.longitude
                  ],
                  [selectedShipment.destination_hub.latitude, selectedShipment.destination_hub.longitude]
                ]}
                pathOptions={{
                  color: selectedShipment.status === 'MISPLACED' ? '#e11d48' : '#2563eb',
                  weight: 4,
                  dashArray: selectedShipment.status === 'MISPLACED' ? '6, 6' : undefined,
                  opacity: 0.9,
                }}
              />
            </React.Fragment>
          )}
        </MapContainer>
      </div>

      {/* Selected Shipment Detail Card (Bottom Right Floating Panel) */}
      {selectedShipment && (
        <div className="absolute bottom-4 right-4 z-[600] w-96 max-w-full bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 transition-all">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-base font-extrabold text-slate-900">
                  {selectedShipment.tracking_number}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    selectedShipment.status === 'MISPLACED'
                      ? 'bg-rose-100 text-rose-700 border border-rose-300'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {selectedShipment.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedShipment.origin_hub?.name || 'Origin'} &rarr; {selectedShipment.destination_hub?.name || 'Destination'}
              </p>
            </div>
            <button
              onClick={() => onSelectShipmentId?.(null)}
              className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 my-3 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            <div>
              <span className="text-slate-400 block text-[10px]">Priority</span>
              <strong className="text-slate-800 font-bold">{selectedShipment.priority}</strong>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Weight</span>
              <strong className="text-slate-800 font-bold">{selectedShipment.weight_kg} kg</strong>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Volume</span>
              <strong className="text-slate-800 font-bold">{selectedShipment.volume_m3 || 1.0} m³</strong>
            </div>
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
              <div className="flex items-center justify-between pt-2 border-t border-emerald-200 text-emerald-900 font-semibold">
                <span>Save ₹{selectedRec.cost_saved.toLocaleString()}</span>
                <button
                  onClick={() => onAcceptRecommendation(selectedRec)}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded-lg shadow-sm flex items-center gap-1"
                >
                  <ShieldCheck className="h-3.5 w-3.5" /> Accept Piggyback
                </button>
              </div>
            </div>
          ) : selectedShipment.status === 'MISPLACED' ? (
            <button
              onClick={() => onSelectTab('planner')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs py-2 px-3 rounded-xl shadow-sm flex items-center justify-center gap-1.5 transition-colors"
            >
              <Navigation className="h-4 w-4" /> Open Recovery Planner
            </button>
          ) : (
            <div className="text-xs text-slate-500 bg-slate-50 p-2 rounded-lg text-center">
              Shipment is on-track. No recovery action required.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
