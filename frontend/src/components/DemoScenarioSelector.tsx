import React, { useState } from 'react';
import { Cpu, ArrowRight, ShieldAlert, Sparkles, UserX, AlertTriangle } from 'lucide-react';
import { loadDemoScenario } from '../services/api';

interface DemoScenarioSelectorProps {
  onSelectCase: (caseId: string) => void;
  onRefreshParent: () => void;
}

export const DemoScenarioSelector: React.FC<DemoScenarioSelectorProps> = ({
  onSelectCase,
  onRefreshParent
}) => {
  const [loadingKey, setLoadingKey] = useState<string | null>(null);

  const scenarios = [
    {
      key: 'successful-recovery',
      caseId: 'SR-1027',
      customer: 'CloudScale Analytics',
      amount: '₹9,999',
      title: 'Scenario 1: End-to-End Auto Recovery Loop',
      badge: 'Primary 30s Demo',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      description: 'Customer D fails -> AI scores 90+ & recommends RETRY -> Guardrails pass -> Retry succeeds -> Workflow automatically stops & recovers ₹9,999.',
      icon: Sparkles,
      iconColor: 'text-emerald-400'
    },
    {
      key: 'guardrail-blocked',
      caseId: 'SR-1026',
      customer: 'Apex Retail Logistics',
      amount: '₹14,999',
      title: 'Scenario 2: Guardrail Overrides AI (Dispute Block)',
      badge: 'Safety Differentiator',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Customer has 10/10 perfect payment history. AI recommends RETRY (85%), but GuardrailEngine detects active dispute and BLOCKS execution.',
      icon: ShieldAlert,
      iconColor: 'text-rose-400'
    },
    {
      key: 'max-attempts',
      caseId: 'SR-1028',
      customer: 'Horizon Media Labs',
      amount: '₹8,499',
      title: 'Scenario 3: Max Attempts Limit (2 Attempts)',
      badge: 'Safe Stopping Rule',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      description: 'Mandate failed twice in current cycle. Rule 1 strictly prohibits further attempts; workflow stops safely and routes to review.',
      icon: AlertTriangle,
      iconColor: 'text-amber-400'
    },
    {
      key: 'customer-opt-out',
      caseId: 'SR-1029',
      customer: 'FinPulse Systems',
      amount: '₹12,500',
      title: 'Scenario 4: Customer Opt-Out Stop',
      badge: 'Compliance Protection',
      badgeColor: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      description: 'Customer explicitly opted out. Rule 4 immediately locks automated debits and safely transitions state to STOPPED.',
      icon: UserX,
      iconColor: 'text-orange-400'
    }
  ];

  const handleLaunch = async (sc: typeof scenarios[0]) => {
    try {
      setLoadingKey(sc.key);
      await loadDemoScenario(sc.key);
      onRefreshParent();
      onSelectCase(sc.caseId);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingKey(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Interactive Hackathon Demo Journeys</h2>
            <p className="text-xs text-slate-400">Deterministic, 1-click test scenarios showcasing AI recommendations and authoritative safety guardrails</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isLoading = loadingKey === sc.key;

          return (
            <div
              key={sc.key}
              className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-all rounded-xl p-5 shadow-lg flex flex-col justify-between space-y-4 group"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      <Icon className={`w-4 h-4 ${sc.iconColor}`} />
                    </div>
                    <div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${sc.badgeColor}`}>
                        {sc.badge}
                      </span>
                      <h3 className="text-sm font-bold text-white mt-1.5">{sc.title}</h3>
                    </div>
                  </div>
                </div>

                <div className="mt-3 text-xs text-slate-300">
                  <span className="font-semibold text-slate-400">Target: </span>
                  <span className="text-white font-medium">{sc.customer}</span> ({sc.amount}) • <span className="font-mono text-blue-400">#{sc.caseId}</span>
                </div>

                <p className="text-xs text-slate-400 mt-2 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                  {sc.description}
                </p>
              </div>

              <button
                onClick={() => handleLaunch(sc)}
                disabled={isLoading}
                className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-blue-600/20 transition-all cursor-pointer disabled:opacity-50"
              >
                <span>{isLoading ? 'Launching Scenario...' : 'Play Scenario Journey'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
