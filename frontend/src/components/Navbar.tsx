import React, { useState } from 'react';
import {
  Shield,
  RefreshCw,
  Activity,
  Layers,
  AlertCircle,
  PlayCircle,
  Cpu,
  CheckCircle2,
  Sparkles,
  Brain,
  Sliders,
  TrendingUp,
  ShieldAlert
} from 'lucide-react';
import { resetDemoData } from '../services/api';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onDataRefresh: () => void;
  pendingReviewsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onDataRefresh,
  pendingReviewsCount
}) => {
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const handleReset = async () => {
    try {
      setResetting(true);
      await resetDemoData();
      setResetSuccess(true);
      onDataRefresh();
      setTimeout(() => setResetSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setResetting(false);
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'priorities', label: 'Revenue Priorities', icon: TrendingUp },
    { id: 'optimizer', label: 'Strategy Optimizer', icon: Sparkles },
    { id: 'failure-intel', label: 'Failure Intel', icon: Brain },
    { id: 'what-if', label: 'What-If Simulator', icon: Sliders },
    { id: 'stress-test', label: 'Safety Stress Test', icon: ShieldAlert },
    { id: 'cases', label: 'Cases', icon: Layers },
    { id: 'human-review', label: 'Human Review', icon: AlertCircle, badge: pendingReviewsCount },
    { id: 'simulator', label: 'Simulator', icon: PlayCircle },
    { id: 'scenarios', label: 'Demo Journeys', icon: Cpu },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#0B0F19]/95 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-2">
          {/* Brand Logo */}
          <div className="flex items-center space-x-2.5 cursor-pointer shrink-0" onClick={() => setActiveTab('dashboard')}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 border border-blue-400/30">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-lg font-bold tracking-tight text-white">SMART<span className="text-blue-500">RECOVER</span></span>
                <span className="text-[9px] uppercase font-bold tracking-wider px-1 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">AI + Guardrails</span>
              </div>
              <p className="text-[10px] text-slate-400 font-medium hidden sm:block">AI Recommends. Guardrails Decide.</p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="flex items-center space-x-1 overflow-x-auto py-1 px-1 flex-1 min-w-0 no-scrollbar bg-slate-900/80 rounded-xl border border-slate-800">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                      isActive ? 'bg-white text-blue-600' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={handleReset}
              disabled={resetting}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                resetSuccess
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
              }`}
              title="Reset database to initial demo state"
            >
              {resetSuccess ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="hidden sm:inline">Reset!</span>
                </>
              ) : (
                <>
                  <RefreshCw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-blue-400' : 'text-slate-400'}`} />
                  <span className="hidden sm:inline">{resetting ? 'Resetting...' : 'Reset'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
