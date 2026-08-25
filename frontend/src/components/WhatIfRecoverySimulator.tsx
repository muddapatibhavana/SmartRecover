import React, { useState, useEffect } from 'react';
import {
  Sliders,
  AlertOctagon,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2
} from 'lucide-react';
import { WhatIfSimulationResponse } from '../types';
import { runWhatIfSimulation } from '../services/api';

interface WhatIfRecoverySimulatorProps {
  initialCaseId?: string;
  onSelectCase?: (caseId: string) => void;
}

export const WhatIfRecoverySimulator: React.FC<WhatIfRecoverySimulatorProps> = ({
  initialCaseId = 'SR-1024',
  onSelectCase
}) => {
  const [selectedCaseId, setSelectedCaseId] = useState<string>(initialCaseId);
  const [simulationData, setSimulationData] = useState<WhatIfSimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const demoCases = [
    { id: 'SR-1024', label: 'SR-1024 — ABC Technologies (₹14,999 • Temporary Timeout)' },
    { id: 'SR-1027', label: 'SR-1027 — CloudScale Analytics (₹9,999 • Processing Timeout)' },
    { id: 'SR-1025', label: 'SR-1025 — BlueWave Dynamics (₹9,999 • Low Score)' },
    { id: 'SR-1026', label: 'SR-1026 — Apex Retail Logistics (₹14,999 • Active Dispute)' },
    { id: 'SR-1028', label: 'SR-1028 — Horizon Media Labs (₹8,499 • Max Retries)' },
    { id: 'SR-1029', label: 'SR-1029 — FinPulse Systems (₹12,500 • Opted Out)' },
  ];

  const handleRunSimulation = async (caseId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await runWhatIfSimulation(caseId);
      setSimulationData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to run What-If simulation');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleRunSimulation(selectedCaseId);
  }, [selectedCaseId]);

  return (
    <div className="space-y-6">
      {/* Simulation Banner */}
      <div className="bg-amber-950/30 border border-amber-500/40 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-amber-300">
        <div className="flex items-center space-x-3">
          <AlertOctagon className="w-5 h-5 text-amber-400 shrink-0" />
          <div className="text-xs">
            <span className="font-bold tracking-wider uppercase text-amber-400">Sandbox Mode: </span>
            <span>{simulationData?.disclaimer || 'SIMULATION — NO PAYMENT WILL BE EXECUTED'}</span>
          </div>
        </div>
        <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
          Hypothetical Analysis
        </span>
      </div>

      {/* Header & Case Selector */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">What-If Recovery Simulator</h2>
            <p className="text-xs text-slate-400">
              Compare recovery probabilities and expected revenue across multiple timing and communication strategies.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            {demoCases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          <button
            onClick={() => handleRunSimulation(selectedCaseId)}
            disabled={loading}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-xs text-rose-300">
          {error}
        </div>
      )}

      {simulationData && (
        <div className="space-y-6">
          {/* Target Info Bar */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400">Simulation Target:</span>
              <span className="font-bold text-white">{simulationData.customer_name}</span>
              <span className="font-mono text-blue-400 font-bold">#{simulationData.case_id}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-slate-400">Recurring Mandate Amount:</span>
              <span className="font-mono font-extrabold text-white text-sm">
                ₹{simulationData.amount.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-slate-400">Failure Code:</span>
              <span className="font-mono px-2 py-0.5 rounded bg-slate-800 text-purple-300 border border-slate-700">
                {simulationData.failure_code}
              </span>
            </div>
          </div>

          {/* Strategies Comparison Table */}
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl shadow-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Strategy Comparison Matrix</h3>
              <span className="text-[11px] text-slate-500 font-mono">5 Pathways Simulated</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] font-bold tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3.5">Recovery Strategy</th>
                    <th className="px-5 py-3.5">Success Probability</th>
                    <th className="px-5 py-3.5">Expected Recovery</th>
                    <th className="px-5 py-3.5">Risk Level</th>
                    <th className="px-5 py-3.5">Customer Contact</th>
                    <th className="px-5 py-3.5">Guardrails</th>
                    <th className="px-5 py-3.5 text-right">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {simulationData.strategies.map((st) => (
                    <tr
                      key={st.strategy}
                      className={`transition-colors ${
                        st.is_recommended
                          ? 'bg-purple-950/20 font-medium'
                          : 'hover:bg-slate-900/40'
                      }`}
                    >
                      <td className="px-5 py-4">
                        <div className="font-bold text-white">{st.label}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">{st.reason}</div>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-slate-800 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                st.success_probability >= 0.70 ? 'bg-emerald-500' :
                                st.success_probability >= 0.40 ? 'bg-amber-500' : 'bg-slate-600'
                              }`}
                              style={{ width: `${st.success_probability * 100}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-slate-200">
                            {Math.round(st.success_probability * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="font-mono font-bold text-emerald-400 text-sm">
                          ₹{st.expected_recovery_amount.toLocaleString('en-IN')}
                        </span>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                          st.risk_level === 'LOW' || st.risk_level === 'ZERO'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}>
                          {st.risk_level}
                        </span>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-slate-400">
                        {st.customer_contact_risk}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        {st.guardrail_allowed ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center w-fit gap-1">
                            <ShieldCheck className="w-3 h-3" /> ALLOWED
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center w-fit gap-1" title={st.guardrail_reason}>
                            <ShieldAlert className="w-3 h-3" /> BLOCKED
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4 text-right whitespace-nowrap">
                        {st.is_recommended ? (
                          <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm">
                            ★ RECOMMENDED
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-500">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* "Why Recommended?" Section */}
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-purple-400">
                <Sparkles className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wider">
                  Why Strategy {simulationData.best_strategy} is Recommended:
                </h3>
              </div>
              {onSelectCase && (
                <button
                  onClick={() => onSelectCase(simulationData.case_id)}
                  className="text-xs font-semibold text-blue-400 hover:text-blue-300 cursor-pointer"
                >
                  Inspect Case #{simulationData.case_id} →
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {simulationData.why_recommended.map((item, i) => (
                <div key={i} className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
