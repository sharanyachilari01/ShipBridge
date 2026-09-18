import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Navbar, TabType } from './components/Navbar';
import { DetectionView } from './components/DetectionView';
import { MapView } from './components/MapView';
import { RecoveryQueueView } from './components/RecoveryQueueView';
import { PlannerView } from './components/PlannerView';
import { ImpactView } from './components/ImpactView';
import { AddShipmentView } from './components/AddShipmentView';
import {
  fetchHubs,
  fetchShipments,
  fetchRoutes,
  fetchPiggybackRecommendations,
  acceptRecoveryPlan
} from './api';
import { Hub, Shipment, VehicleRoute, PiggybackRecommendation } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('map');
  const [selectedShipmentId, setSelectedShipmentId] = useState<number | null>(null);
  const [hubs, setHubs] = useState<Hub[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [routes, setRoutes] = useState<VehicleRoute[]>([]);
  const [recommendations, setRecommendations] = useState<PiggybackRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = useCallback(async () => {
    try {
      const [hubsData, shipmentsData, routesData, recsData] = await Promise.all([
        fetchHubs(),
        fetchShipments(),
        fetchRoutes(),
        fetchPiggybackRecommendations(),
      ]);
      setHubs(hubsData);
      setShipments(shipmentsData);
      setRoutes(routesData);
      setRecommendations(recsData);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAcceptRecommendation = async (rec: PiggybackRecommendation) => {
    try {
      await acceptRecoveryPlan({
        shipment_id: rec.shipment.id,
        vehicle_route_id: rec.vehicle_route.id,
        pickup_hub_id: rec.pickup_hub.id,
        dropoff_hub_id: rec.dropoff_hub.id,
        cost_saved: rec.cost_saved,
        co2_saved_kg: rec.co2_saved_kg,
        explanation: rec.explanation,
      });

      await loadData();
      alert(`Piggyback Recovery accepted! Shipment ${rec.shipment.tracking_number} assigned to Route ${rec.vehicle_route.vehicle_code}.`);
    } catch (e) {
      alert('Failed to accept recovery plan');
    }
  };

  const handleShipmentCreated = (newShipment: Shipment) => {
    loadData();
    setSelectedShipmentId(newShipment.id);
    setActiveTab('map');
  };

  const misplacedCount = shipments.filter((s) => s.status === 'MISPLACED').length;
  const onTrackCount = shipments.filter((s) => s.status !== 'MISPLACED').length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Header Bar */}
      <Header
        misplacedCount={misplacedCount}
        onTrackCount={onTrackCount}
        onRefreshData={loadData}
      />

      {/* Main View Area */}
      <main className="flex-1 overflow-x-hidden pb-16">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)] text-slate-500 font-medium">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-3" />
            <span>Loading ShipBridge Command Center Data...</span>
          </div>
        ) : (
          <>
            {activeTab === 'map' && (
              <MapView
                hubs={hubs}
                shipments={shipments}
                routes={routes}
                recommendations={recommendations}
                selectedShipmentId={selectedShipmentId}
                onSelectShipmentId={setSelectedShipmentId}
                onAcceptRecommendation={handleAcceptRecommendation}
                onSelectTab={(tab) => setActiveTab(tab)}
              />
            )}
            {activeTab === 'queue' && (
              <RecoveryQueueView
                shipments={shipments}
                recommendations={recommendations}
                onSelectShipmentId={(id) => {
                  setSelectedShipmentId(id);
                  setActiveTab('map');
                }}
                onAcceptRecommendation={handleAcceptRecommendation}
                onSelectTab={(tab) => setActiveTab(tab)}
              />
            )}
            {activeTab === 'planner' && (
              <PlannerView
                shipments={shipments}
                routes={routes}
                recommendations={recommendations}
                selectedShipmentId={selectedShipmentId}
                onSelectShipmentId={setSelectedShipmentId}
                onAcceptRecommendation={handleAcceptRecommendation}
              />
            )}
            {activeTab === 'impact' && <ImpactView />}
            {activeTab === 'add' && (
              <AddShipmentView
                hubs={hubs}
                onShipmentCreated={handleShipmentCreated}
                onSelectTab={(tab) => setActiveTab(tab)}
              />
            )}
            {activeTab === 'detection' && (
              <DetectionView
                onSelectShipmentId={(id) => {
                  setSelectedShipmentId(id);
                  setActiveTab('planner');
                }}
              />
            )}
          </>
        )}
      </main>


      {/* Fixed Bottom Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        misplacedCount={misplacedCount}
      />
    </div>
  );
};

export default App;
