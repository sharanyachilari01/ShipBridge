import React from 'react';
import { AlertTriangle, CheckCircle2, Truck } from 'lucide-react';

interface HeaderProps {
  misplacedCount: number;
  onTrackCount: number;
  onRefreshData?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ misplacedCount, onTrackCount }) => {
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Truck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">ShipBridge</h1>
              <span className="text-[11px] bg-blue-500/20 text-blue-300 font-semibold px-2 py-0.5 rounded border border-blue-400/30">
                Logistics Control Tower
              </span>
            </div>
            <p className="text-xs text-slate-400">Intelligent Shipment Piggybacking & Recovery Network</p>
          </div>
        </div>

        {/* Live Operational Counters */}
        <div className="flex items-center flex-wrap gap-3 text-xs">
          <div className="flex items-center gap-2 bg-slate-800/90 border border-slate-700/70 rounded-xl px-3.5 py-1.5 shadow-inner">
            <span className="text-slate-400 font-medium flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
              Misplaced:
            </span>
            <span className="font-extrabold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-md text-xs">
              {misplacedCount}
            </span>

            <span className="text-slate-600">|</span>

            <span className="text-slate-400 font-medium flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              On-Track:
            </span>
            <span className="font-extrabold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md text-xs">
              {onTrackCount}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
