import React, { useEffect, useState } from 'react';
import { fetchHealth, triggerSeedData } from '../api';
import { BackendHealth } from '../types';
import { Activity, RefreshCw, AlertTriangle, CheckCircle2, ShieldCheck, Truck } from 'lucide-react';

interface HeaderProps {
  misplacedCount: number;
  onTrackCount: number;
  onRefreshData: () => void;
}

export const Header: React.FC<HeaderProps> = ({ misplacedCount, onTrackCount, onRefreshData }) => {
  const [health, setHealth] = useState<BackendHealth>({ status: 'offline' });
  const [loading, setLoading] = useState<boolean>(false);
  const [seeding, setSeeding] = useState<boolean>(false);

  const checkHealthStatus = async () => {
    setLoading(true);
    const data = await fetchHealth();
    setHealth(data);
    setLoading(false);
  };

  useEffect(() => {
    checkHealthStatus();
    const interval = setInterval(checkHealthStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSeed = async () => {
    if (confirm('Reset network with sample hubs, misplaced shipments, and active routes?')) {
      setSeeding(true);
      try {
        await triggerSeedData();
        await checkHealthStatus();
        onRefreshData();
      } catch (e) {
        alert('Failed to reset sample data');
      } finally {
        setSeeding(false);
      }
    }
  };

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Logo & Product Title */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Truck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">ShipBridge</h1>
              <span className="text-xs bg-blue-500/20 text-blue-300 font-medium px-2 py-0.5 rounded border border-blue-400/30">
                Piggyback Engine v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">Intelligent Recovery & Network Logistics Command Center</p>
          </div>
        </div>

        {/* Status Indicators & Seed Button */}
        <div className="flex items-center flex-wrap gap-2 text-sm">
          {/* Health Badge */}
          <div
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              health.status === 'ok'
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-700/50'
                : 'bg-rose-950/80 text-rose-400 border-rose-700/50'
            }`}
          >
            {health.status === 'ok' ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>Backend Health: <strong>OK</strong></span>
              </>
            ) : (
              <>
                <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                <span>Backend Health: <strong>Offline</strong></span>
              </>
            )}
          </div>

          {/* Quick Metrics Badges */}
          <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1">
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
              Misplaced:
            </span>
            <span className="text-xs font-bold text-rose-500 bg-rose-500/10 px-1.5 py-0.5 rounded">
              {misplacedCount}
            </span>

            <span className="text-slate-600">|</span>

            <span className="text-xs text-slate-400 flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              On-Track:
            </span>
            <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
              {onTrackCount}
            </span>
          </div>

          {/* Reload / Seed Data Button */}
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-3 py-1.5 rounded-lg border border-slate-700 transition-colors"
            title="Reset sample network & seed data"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${seeding ? 'animate-spin' : ''}`} />
            <span>{seeding ? 'Resetting...' : 'Reset Seed Data'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
