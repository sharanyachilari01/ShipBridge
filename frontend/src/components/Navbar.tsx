import React from 'react';
import { Map, AlertCircle, Compass, BarChart3, PlusCircle, ShieldAlert } from 'lucide-react';

export type TabType = 'map' | 'queue' | 'planner' | 'impact' | 'add' | 'detection';

interface NavbarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  misplacedCount: number;
}

interface NavTab {
  id: TabType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onSelectTab, misplacedCount }) => {
  const tabs: NavTab[] = [
    { id: 'map', label: 'Map', icon: Map },
    { id: 'queue', label: 'Recovery Queue', icon: AlertCircle, badge: misplacedCount },
    { id: 'planner', label: 'Planner', icon: Compass },
    { id: 'impact', label: 'Network Impact', icon: BarChart3 },
    { id: 'add', label: 'Add Shipment', icon: PlusCircle },
    { id: 'detection', label: 'Detection Evidence', icon: ShieldAlert },
  ];


  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-slate-200 shadow-lg">
      <div className="max-w-4xl mx-auto px-2">
        <div className="flex justify-around items-center h-16">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id as TabType)}
                className={`relative flex flex-col items-center justify-center w-full h-full px-2 transition-all ${
                  isActive
                    ? 'text-blue-600 font-semibold border-t-2 border-blue-600 -mt-[2px]'
                    : 'text-slate-500 hover:text-slate-900 font-medium'
                }`}
              >
                <div className="relative">
                  <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
                  {tab.badge !== undefined && tab.badge > 0 && (
                    <span className="absolute -top-1.5 -right-2.5 bg-rose-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full min-w-[16px] text-center shadow-sm">
                      {tab.badge}
                    </span>
                  )}
                </div>
                <span className="text-xs mt-1 tracking-tight">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
