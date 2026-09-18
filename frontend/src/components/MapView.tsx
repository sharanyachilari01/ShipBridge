import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
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
  Flame
} from 'lucide-react';

interface MapViewProps {
  hubs: Hub[];
  shipments: Shipment[];
  routes: VehicleRoute[];
  recommendations: PiggybackRecommendation[];
  onAcceptRecommendation: (rec: PiggybackRecommendation) => void;
  onSelectTab: (tab: 'queue' | 'planner') => void;
}

// 1. Hub Marker (Slate/Blue-Gray Depot Icon)
const createHubIcon = (code: string) => {
  return L.divIcon({
    className: 'custom-hub-icon',
    html: `<div style="background-color: #0f172a; color: white; border: 2px solid #3b82f6; border-radius: 8px; padding: 2px 5px; font-size: 10px; font-weight: bold; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 3px;">
            <span style="color: #60a5fa;">🏛️</span> ${code}
          </div>`,
    iconSize: [65, 24],
    iconAnchor: [32, 12],
  });
};

// 2. Original Custom 3D / Isometric Dark Cargo Truck Marker (Charcoal/Blue-Gray with soft shadow)
const createTruckIcon = (code: string) => {
  return L.divIcon({
    className: 'custom-truck-3d-icon',
    html: `
      <div style="position: relative; display: flex; flex-direction: column; items-center; transition: transform 0.2s ease;">
        <!-- Isometric Dark Truck SVG -->
        <svg width="44" height="30" viewBox="0 0 44 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 5px 6px rgba(15, 23, 42, 0.45));">
          <!-- Soft Ground Shadow -->
          <ellipse cx="22" cy="27" rx="18" ry="3.5" fill="#0f172a" fill-opacity="0.4"/>
          
          <!-- Cargo Container Body (Charcoal/Slate) -->
          <polygon points="5,8 26,2 36,6 15,12" fill="#475569" stroke="#1e293b" stroke-width="0.8"/>
          <polygon points="5,8 15,12 15,22 5,18" fill="#334155" stroke="#1e293b" stroke-width="0.8"/>
          <polygon points="15,12 36,6 36,16 15,22" fill="#1e293b" stroke="#0f172a" stroke-width="0.8"/>
          
          <!-- Truck Cab (Driver Front) -->
          <polygon points="32,13 39,11 42,14 35,16" fill="#64748b" stroke="#1e293b" stroke-width="0.7"/>
          <polygon points="35,16 42,14 42,20 35,22" fill="#38bdf8" fill-opacity="0.8" stroke="#1e293b" stroke-width="0.7"/>
          <polygon points="28,14 35,16 35,22 28,20" fill="#334155" stroke="#1e293b" stroke-width="0.7"/>

          <!-- Isometric Wheels -->
          <ellipse cx="10" cy="20" rx="3.2" ry="4" fill="#0f172a" stroke="#64748b" stroke-width="0.8"/>
          <ellipse cx="21" cy="23" rx="3.2" ry="4" fill="#0f172a" stroke="#64748b" stroke-width="0.8"/>
          <ellipse cx="36" cy="20" rx="2.8" ry="3.5" fill="#0f172a" stroke="#64748b" stroke-width="0.8"/>
        </svg>
        <span style="background-color: #1e293b; color: #f8fafc; border: 1px solid #475569; border-radius: 4px; padding: 1px 4px; font-size: 9px; font-weight: bold; margin-top: -4px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); white-space: nowrap;">
          ${code}
        </span>
      </div>
    `,
    iconSize: [46, 42],
    iconAnchor: [23, 21],
  });
};

// 3. Misplaced Shipment Marker (RED ONLY)
const createMisplacedIcon = () => {
  return L.divIcon({
    className: 'custom-misplaced-icon',
    html: `<div style="background-color: #e11d48; color: white; border: 2px solid white; border-radius: 9999px; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; box-shadow: 0 4px 10px rgba(225,29,72,0.6); animation: pulse 2s infinite;">
            ⚠️
          </div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
};

// 4. High Priority Shipment Marker (Amber)
const createHighPriorityIcon = () => {
  return L.divIcon({
    className: 'custom-priority-icon',
    html: `<div style="background-color: #f59e0b; color: white; border: 2px solid white; border-radius: 9999px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; box-shadow: 0 3px 6px rgba(245,158,11,0.5);">
            ⚡
          </div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

// 5. Delayed Shipment Marker (Orange Clock)
const createDelayedIcon = () => {
  return L.divIcon({
    className: 'custom-delayed-icon',
    html: `<div style="background-color: #ea580c; color: white; border: 2px solid white; border-radius: 9999px; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; box-shadow: 0 3px 6px rgba(234,88,12,0.5);">
            ⏱️
          </div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

// 6. On-Track Shipment Marker (Green)
const createOnTrackIcon = () => {
  return L.divIcon({
    className: 'custom-ontrack-icon',
    html: `<div style="background-color: #059669; color: white; border: 2px solid white; border-radius: 9999px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
            ✓
          </div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

export const MapView: React.FC<MapViewProps> = ({
  hubs,
  shipments,
  routes,
  recommendations,
  onAcceptRecommendation,
  onSelectTab,
}) => {
  const [filterMode, setFilterMode] = useState<'all' | 'misplaced' | 'routes'>('all');
  const [selectedShipment, setSelectedShipment] = useState<Shipment | null>(null);

  // Center map on India geographic center
  const centerLat = 20.5937;
  const centerLng = 78.9629;
  const defaultZoom = 5;

  const misplacedShipments = shipments.filter((s) => s.status === 'MISPLACED');
  const delayedShipments = shipments.filter((s) => s.status === 'DELAYED');
  const onTrackShipments = shipments.filter((s) => s.status === 'ON_TRACK' || s.status === 'RECOVERING');

  return (
    <div className="relative w-full h-[calc(100vh-8.5rem)] bg-slate-100 flex flex-col">
      {/* Map Filter Bar */}
      <div className="absolute top-4 left-4 z-[500] bg-white/95 backdrop-blur-md p-2 rounded-xl shadow-lg border border-slate-200/80 flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-700 ml-1">India Network:</span>
        <button
          onClick={() => setFilterMode('all')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
            filterMode === 'all'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          All Layers ({hubs.length} Hubs)
        </button>
        <button
          onClick={() => setFilterMode('misplaced')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
            filterMode === 'misplaced'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          <AlertTriangle className="h-3 w-3" />
          Misplaced ({misplacedShipments.length})
        </button>
        <button
          onClick={() => setFilterMode('routes')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
            filterMode === 'routes'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          <Truck className="h-3 w-3" />
          Active Corridors ({routes.length})
        </button>
      </div>

      {/* Map Legend Overlay */}
      <div className="absolute top-4 right-4 z-[500] bg-slate-900/95 text-white p-3.5 rounded-2xl shadow-xl border border-slate-700 max-w-xs">
        <div className="text-xs font-bold text-slate-200 mb-2 border-b border-slate-800 pb-1.5 flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 text-blue-400" />
          India Network Legend
        </div>
        <div className="space-y-1.5 text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-slate-800 border border-blue-500 flex items-center justify-center text-[10px]">🏛️</span>
            <span><strong>Logistics Hub</strong> (26 National Depots)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-slate-700 border border-slate-500 flex items-center justify-center text-[10px]">🚚</span>
            <span><strong>Active Truck</strong> (3D Isometric Icon)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded-full bg-rose-600 text-white flex items-center justify-center text-[10px] font-bold">⚠️</span>
            <span><strong>Misplaced Shipment</strong> (Red Alert)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded-full bg-amber-500 text-white flex items-center justify-center text-[10px] font-bold">⚡</span>
            <span><strong>High Priority Shipment</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded-full bg-orange-600 text-white flex items-center justify-center text-[10px] font-bold">⏱️</span>
            <span><strong>Delayed Shipment</strong></span>
          </div>
        </div>
      </div>

      {/* Leaflet Map Container */}
      <div className="w-full flex-1 relative">
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={defaultZoom}
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Hub Markers */}
          {filterMode !== 'routes' &&
            hubs.map((hub) => (
              <Marker key={`hub-${hub.id}`} position={[hub.latitude, hub.longitude]} icon={createHubIcon(hub.code)}>
                <Popup>
                  <div className="p-1 max-w-xs">
                    <div className="font-bold text-slate-900 text-sm flex items-center gap-1">
                      <Building2 className="h-4 w-4 text-blue-600" />
                      {hub.name}
                    </div>
                    <div className="text-xs text-slate-600 mt-1">Code: <strong>{hub.code}</strong></div>
                    <div className="text-xs text-slate-600">Location: {hub.city}, {hub.state}</div>
                    <div className="text-[11px] text-slate-400 mt-1 italic">
                      Synthetic Demo Data
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* Vehicle Routes (Corridor Lines & Isometric 3D Truck Markers) */}
          {(filterMode === 'all' || filterMode === 'routes') &&
            routes.map((route) => {
              const positions: [number, number][] = route.waypoints
                .filter((wp) => wp.lat && wp.lng)
                .map((wp) => [wp.lat, wp.lng]);

              if (positions.length < 2) return null;

              return (
                <React.Fragment key={`route-group-${route.id}`}>
                  <Polyline
                    positions={positions}
                    pathOptions={{ color: '#2563eb', weight: 3.5, opacity: 0.75, dashArray: '6, 6' }}
                  >
                    <Tooltip sticky>
                      <div className="text-xs font-semibold">
                        Freight Corridor: {route.vehicle_code}<br />
                        Driver: {route.driver_name}<br />
                        Spare Capacity: {route.spare_capacity_kg} kg
                      </div>
                    </Tooltip>
                  </Polyline>

                  {/* 3D Isometric Dark Truck Marker at primary waypoint */}
                  {positions[0] && (
                    <Marker position={positions[0]} icon={createTruckIcon(route.vehicle_code)}>
                      <Popup>
                        <div className="p-1">
                          <div className="font-bold text-slate-900 text-sm flex items-center gap-1">
                            <Truck className="h-4 w-4 text-blue-600" />
                            {route.vehicle_code}
                          </div>
                          <div className="text-xs text-slate-600 mt-0.5">{route.vehicle_type}</div>
                          <div className="text-xs text-slate-600">Driver: <strong>{route.driver_name}</strong></div>
                          <div className="text-xs font-semibold text-emerald-600 mt-1">
                            Available Capacity: {route.spare_capacity_kg} kg
                          </div>
                        </div>
                      </Popup>
                    </Marker>
                  )}
                </React.Fragment>
              );
            })}

          {/* Misplaced Shipment Markers (RED ONLY) */}
          {filterMode !== 'routes' &&
            misplacedShipments.map((shp) => {
              const lat = shp.current_lat || shp.origin_hub?.latitude || 17.3850;
              const lng = shp.current_lng || shp.origin_hub?.longitude || 78.4867;
              const rec = recommendations.find((r) => r.shipment.id === shp.id);

              return (
                <Marker
                  key={`misplaced-${shp.id}`}
                  position={[lat, lng]}
                  icon={createMisplacedIcon()}
                  eventHandlers={{
                    click: () => setSelectedShipment(shp),
                  }}
                >
                  <Popup>
                    <div className="p-1 max-w-sm">
                      <div className="flex items-center gap-1 text-xs font-bold text-rose-600">
                        <AlertTriangle className="h-4 w-4" />
                        MISPLACED SHIPMENT ALERT
                      </div>
                      <div className="text-sm font-bold text-slate-900 mt-1">{shp.tracking_number}</div>
                      <div className="text-xs text-slate-600 mt-0.5">
                        Destination: <strong>{shp.destination_hub?.name || 'Delhi Hub'}</strong>
                      </div>
                      <div className="text-xs text-slate-600">Weight: {shp.weight_kg} kg | Priority: {shp.priority}</div>

                      {rec && (
                        <div className="mt-2 pt-2 border-t border-slate-200">
                          <div className="text-xs font-bold text-emerald-700 flex items-center justify-between">
                            <span>Piggyback Available:</span>
                            <span className="bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded text-[10px]">
                              Match {rec.match_score}%
                            </span>
                          </div>
                          <div className="text-xs text-slate-600 mt-1">
                            Route <strong>{rec.vehicle_route.vehicle_code}</strong> saves{' '}
                            <strong className="text-emerald-600">₹{rec.cost_saved}</strong> &{' '}
                            <strong className="text-emerald-600">{rec.co2_saved_kg}kg CO2</strong>
                          </div>
                          <button
                            onClick={() => onAcceptRecommendation(rec)}
                            className="mt-2 w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs py-1.5 px-2 rounded-lg flex items-center justify-center gap-1 shadow-sm transition-colors"
                          >
                            <ShieldCheck className="h-3.5 w-3.5" />
                            Accept Piggyback Recovery
                          </button>
                        </div>
                      )}
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {/* Delayed Shipments (Amber Clock Icon) */}
          {filterMode === 'all' &&
            delayedShipments.map((shp) => {
              const lat = shp.current_lat || shp.origin_hub?.latitude || 13.0827;
              const lng = shp.current_lng || shp.origin_hub?.longitude || 80.2707;

              return (
                <Marker key={`delayed-${shp.id}`} position={[lat, lng]} icon={createDelayedIcon()}>
                  <Popup>
                    <div className="p-1">
                      <div className="flex items-center gap-1 text-xs font-bold text-orange-600">
                        <Clock className="h-4 w-4" />
                        SHIPMENT DELAYED
                      </div>
                      <div className="text-sm font-bold text-slate-900 mt-0.5">{shp.tracking_number}</div>
                      <div className="text-xs text-slate-600">Target: {shp.destination_hub?.name}</div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {/* On Track Shipments (Green Check Icon) */}
          {filterMode === 'all' &&
            onTrackShipments.map((shp) => {
              const lat = shp.current_lat || shp.origin_hub?.latitude || 19.0760;
              const lng = shp.current_lng || shp.origin_hub?.longitude || 72.8777;

              return (
                <Marker key={`ontrack-${shp.id}`} position={[lat, lng]} icon={createOnTrackIcon()}>
                  <Popup>
                    <div className="p-1">
                      <div className="flex items-center gap-1 text-xs font-bold text-emerald-600">
                        <CheckCircle2 className="h-4 w-4" />
                        {shp.status === 'RECOVERING' ? 'RECOVERY IN PROGRESS' : 'ON TRACK'}
                      </div>
                      <div className="text-sm font-bold text-slate-900 mt-0.5">{shp.tracking_number}</div>
                      <div className="text-xs text-slate-600">Weight: {shp.weight_kg} kg</div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
        </MapContainer>
      </div>

      {/* Selected Shipment Drawer / Bottom Banner */}
      {selectedShipment && (
        <div className="absolute bottom-4 left-4 right-4 z-[600] max-w-xl mx-auto bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 transition-all">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-lg bg-rose-100 text-rose-600">
                <AlertTriangle className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  {selectedShipment.tracking_number}
                  <span className="text-xs bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-semibold">
                    MISPLACED
                  </span>
                </h3>
                <p className="text-xs text-slate-500">
                  Current Hub: {selectedShipment.expected_next_hub?.name || 'Hyderabad Hub'} &rarr; Target:{' '}
                  {selectedShipment.destination_hub?.name || 'Delhi Hub'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelectedShipment(null)}
              className="text-slate-400 hover:text-slate-600 text-sm font-bold px-2 py-1"
            >
              ✕
            </button>
          </div>

          {/* Piggyback option for selected shipment */}
          {(() => {
            const rec = recommendations.find((r) => r.shipment.id === selectedShipment.id);
            if (!rec) {
              return (
                <div className="mt-3 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
                  <span>Searching active candidate routes...</span>
                  <button
                    onClick={() => onSelectTab('queue')}
                    className="text-blue-600 hover:underline font-semibold flex items-center gap-1"
                  >
                    View Queue <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              );
            }

            return (
              <div className="mt-3 bg-emerald-50/80 border border-emerald-200 rounded-xl p-3">
                <div className="flex items-center justify-between text-xs font-semibold text-emerald-900 mb-1">
                  <span>Best Piggyback Route: {rec.vehicle_route.vehicle_code}</span>
                  <span className="bg-emerald-600 text-white px-2 py-0.5 rounded text-[10px]">
                    Match Score: {rec.match_score}%
                  </span>
                </div>
                <p className="text-xs text-emerald-800 line-clamp-2">{rec.explanation}</p>
                <div className="mt-2 flex items-center justify-between pt-2 border-t border-emerald-200/60">
                  <div className="text-xs">
                    <span className="text-slate-600">Savings: </span>
                    <span className="font-bold text-emerald-700">₹{rec.cost_saved}</span>
                    <span className="text-slate-400"> | </span>
                    <span className="font-bold text-emerald-700">{rec.co2_saved_kg}kg CO2</span>
                  </div>
                  <button
                    onClick={() => {
                      onAcceptRecommendation(rec);
                      setSelectedShipment(null);
                    }}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-1.5 px-3 rounded-lg shadow-sm flex items-center gap-1"
                  >
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Assign Piggyback Now
                  </button>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};
