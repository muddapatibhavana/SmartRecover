import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Info
} from 'lucide-react';
import { StrategyOptimizerResponse } from '../types';
import { optimizeStrategy } from '../services/api';

interface RecoveryStrategyOptimizerProps {
  initialCaseId?: string;
  onSelectCase?: (caseId: string) => void;
}

export const RecoveryStrategyOptimizer: React.FC<RecoveryStrategyOptimizerProps> = ({
  initialCaseId = 'SR-1024',
  onSelectCase
}) => {
  const [selectedCaseId, setSelectedCaseId] = useState<string>(initialCaseId);
  const [optimizerData, setOptimizerData] = useState<StrategyOptimizerResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const demoCases = [
    { id: 'SR-1024', label: 'SR-1024 — ABC Technologies (₹14,999 • Temporary Timeout)' },
    { id: 'SR-1027', label: 'SR-1027 — CloudScale Analytics (₹9,999 • Processing Timeout)' },
    { id: 'SR-1025', label: 'SR-1025 — BlueWave Dynamics (₹9,999 • Low Score / Inactive)' },
    { id: 'SR-1026', label: 'SR-1026 — Apex Retail Logistics (₹14,999 • Active Dispute)' },
    { id: 'SR-1028', label: 'SR-1028 — Horizon Media Labs (₹8,499 • Max Retries Reached)' },
    { id: 'SR-1029', label: 'SR-1029 — FinPulse Systems (₹12,500 • Customer Opt-Out)' },
  ];

  const handleRunOptimizer = async (caseId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await optimizeStrategy(caseId);
      setOptimizerData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to optimize recovery strategy');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleRunOptimizer(selectedCaseId);
  }, [selectedCaseId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Recovery Strategy Optimizer</h2>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                Decision Support
              </span>
            </div>
            <p className="text-xs text-slate-400">
              AI evaluates customer history, failure telemetry, and risk signals to recommend structured recovery strategies.
            </p>
          </div>
        </div>

        {/* Case Selector */}
        <div className="flex items-center space-x-2">
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
          >
            {demoCases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          <button
            onClick={() => handleRunOptimizer(selectedCaseId)}
            disabled={loading}
            className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Optimizing...' : 'Re-Optimize'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-xs text-rose-300">
          {error}
        </div>
      )}

      {optimizerData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Strategy Hero Card */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Recommended Strategy:</span>
                  <div className="text-2xl font-extrabold text-white mt-1 flex items-center gap-2">
                    <span>{optimizerData.strategy_label}</span>
                    <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-900 text-purple-300 border border-purple-500/30">
                      {optimizerData.strategy}
                    </span>
                  </div>
                </div>

                <div className={`px-3 py-1.5 rounded-lg text-xs font-bold border flex items-center space-x-1.5 ${
                  optimizerData.guardrail_precheck_status === 'ALLOWED'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : optimizerData.guardrail_precheck_status === 'BLOCKED'
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}>
                  {optimizerData.guardrail_precheck_status === 'ALLOWED' ? (
                    <ShieldCheck className="w-4 h-4" />
                  ) : (
                    <ShieldAlert className="w-4 h-4" />
                  )}
                  <span>Guardrails: {optimizerData.guardrail_precheck_status}</span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500">Recovery Score</span>
                  <div className="text-xl font-mono font-bold text-white mt-1">
                    {optimizerData.recovery_score}<span className="text-xs text-slate-500">/100</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div
                      className={`h-full ${
                        optimizerData.recovery_score >= 80 ? 'bg-emerald-500' :
                        optimizerData.recovery_score >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${optimizerData.recovery_score}%` }}
                    />
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500">Success Probability</span>
                  <div className="text-xl font-mono font-bold text-emerald-400 mt-1">
                    {Math.round(optimizerData.estimated_success_probability * 100)}%
                  </div>
                  <span className="text-[10px] text-slate-500">Estimated Clearance</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500">Expected Recovery</span>
                  <div className="text-xl font-mono font-bold text-blue-400 mt-1">
                    ₹{optimizerData.expected_recovery_amount.toLocaleString('en-IN')}
                  </div>
                  <span className="text-[10px] text-slate-500">Amt × Probability</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500">AI Confidence</span>
                  <div className="text-xl font-mono font-bold text-purple-400 mt-1">
                    {Math.round(optimizerData.confidence * 100)}%
                  </div>
                  <span className="text-[10px] text-slate-500">Telemetry Depth</span>
                </div>
              </div>

              {/* Reasoning Points */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider">AI Optimizer Reasoning:</span>
                <div className="space-y-1.5">
                  {optimizerData.reasoning.map((r, i) => (
                    <div key={i} className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
                      <ArrowRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Positive vs Negative Factors */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/30 space-y-2">
                  <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Positive Recovery Signals</span>
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {optimizerData.positive_factors.length > 0 ? (
                      optimizerData.positive_factors.map((f, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-emerald-400 font-bold">•</span>
                          <span>{f}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-slate-500 text-xs">No dominant positive signals detected</li>
                    )}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/30 space-y-2">
                  <div className="flex items-center space-x-1.5 text-rose-400 text-xs font-bold">
                    <XCircle className="w-4 h-4" />
                    <span>Risk Signals & Penalties</span>
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {optimizerData.negative_factors.length > 0 ? (
                      optimizerData.negative_factors.map((f, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-rose-400 font-bold">•</span>
                          <span>{f}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-slate-500 text-xs">No risk penalties active</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Right Architecture & Policy Panel */}
          <div className="space-y-6">
            <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 shadow-xl space-y-4">
              <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
                <Info className="w-4 h-4 text-blue-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Strategy Execution Policy</h3>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <span className="font-semibold text-slate-400">Decision Support Rule:</span>
                  <p className="text-slate-300">
                    The Recovery Strategy Optimizer is advisory. Every proposed strategy is validated through the 10 deterministic rules of the GuardrailEngine before execution.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <span className="font-semibold text-slate-400">Cooldown Policy:</span>
                  <p className="text-slate-300">
                    Recommended delay: <span className="font-mono font-bold text-purple-400">{optimizerData.recommended_delay_hours} hours</span>. Standard NPCI clearing protocol enforces a minimum 24-hour interval between recurring mandate retries.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <span className="font-semibold text-slate-400">Human Review Threshold:</span>
                  <p className="text-slate-300">
                    Status: <span className={`font-bold ${optimizerData.human_review_required ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {optimizerData.human_review_required ? 'Required (Flagged)' : 'Not Required (Automated)'}
                    </span>
                  </p>
                </div>
              </div>

              {onSelectCase && (
                <button
                  onClick={() => onSelectCase(selectedCaseId)}
                  className="w-full py-2.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 font-semibold text-xs transition-all cursor-pointer text-center"
                >
                  Open Full Case Details →
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
