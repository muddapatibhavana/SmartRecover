import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  ShieldCheck,
  ShieldAlert,
  Search,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { RevenuePriorityMetrics, PriorityCaseSummary } from '../types';
import { fetchRevenuePriorities } from '../services/api';

interface RevenuePriorityDashboardProps {
  onSelectCase: (caseId: string) => void;
}

export const RevenuePriorityDashboard: React.FC<RevenuePriorityDashboardProps> = ({
  onSelectCase
}) => {
  const [metrics, setMetrics] = useState<RevenuePriorityMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTier, setSelectedTier] = useState<string>('ALL');

  const loadPriorities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchRevenuePriorities(50);
      setMetrics(data);
    } catch (err: any) {
      console.error('Failed to load revenue priorities:', err);
      setError(err?.message || 'Failed to load revenue priorities');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPriorities();
  }, [loadPriorities]);

  const topOpportunities: PriorityCaseSummary[] = metrics?.top_opportunities || [];

  const filteredOpportunities = topOpportunities.filter((item) => {
    const itemTier = (item.priority_tier || '').toUpperCase();
    const matchesTier = selectedTier === 'ALL' || itemTier === selectedTier.toUpperCase();
    
    const query = searchQuery.trim().toLowerCase();
    if (!query) return matchesTier;

    const matchesSearch =
      (item.customer_name && item.customer_name.toLowerCase().includes(query)) ||
      (item.customer_email && item.customer_email.toLowerCase().includes(query)) ||
      (item.id && item.id.toLowerCase().includes(query)) ||
      (item.failure_reason && item.failure_reason.toLowerCase().includes(query)) ||
      (item.failure_code && item.failure_code.toLowerCase().includes(query)) ||
      (item.recommended_strategy && item.recommended_strategy.toLowerCase().includes(query));

    return matchesTier && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Revenue-at-Risk Prioritization</h2>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Expected Value Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Ranks failed payments by Expected Recovered Revenue (Amount × Probability) combined with customer reliability and safety signals.
            </p>
          </div>
        </div>

        <button
          onClick={loadPriorities}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-semibold transition-all cursor-pointer disabled:opacity-50 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : 'text-slate-400'}`} />
          <span>{loading ? 'Refreshing...' : 'Refresh Priorities'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadPriorities}
            className="text-xs underline font-semibold hover:text-white"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Priority Summary KPI Cards */}
      {metrics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Revenue at Risk</span>
            <div className="text-2xl font-extrabold text-white font-mono mt-1">
              ₹{metrics.total_revenue_at_risk.toLocaleString('en-IN')}
            </div>
            <span className="text-[10px] text-slate-500">Unrecovered Active Mandates</span>
          </div>

          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 shadow-lg">
            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Expected Recoverable</span>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono mt-1">
              ₹{metrics.expected_recoverable_revenue.toLocaleString('en-IN')}
            </div>
            <span className="text-[10px] text-slate-500">Sum of (Amount × Probability)</span>
          </div>

          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 shadow-lg">
            <span className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider">High Priority Volume</span>
            <div className="text-2xl font-extrabold text-purple-300 font-mono mt-1">
              ₹{metrics.high_priority_amount.toLocaleString('en-IN')}
            </div>
            <span className="text-[10px] text-slate-400">{metrics.high_priority_count} High Probability Accounts</span>
          </div>

          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 shadow-lg">
            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider">Medium Priority Volume</span>
            <div className="text-2xl font-extrabold text-blue-300 font-mono mt-1">
              ₹{metrics.medium_priority_amount.toLocaleString('en-IN')}
            </div>
            <span className="text-[10px] text-slate-400">{metrics.medium_priority_count} Moderate Recovery Accounts</span>
          </div>
        </div>
      )}

      {/* Top Recovery Opportunities Table */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl shadow-xl overflow-hidden space-y-4 p-5">
        {/* Table Filters Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2 w-full sm:w-80">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search priority cases..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex items-center space-x-1.5 self-end sm:self-auto">
            {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((tier) => (
              <button
                key={tier}
                onClick={() => setSelectedTier(tier)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  selectedTier === tier
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                }`}
              >
                {tier}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] font-bold tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-4 py-3.5">Rank</th>
                <th className="px-4 py-3.5">Case / Customer</th>
                <th className="px-4 py-3.5">Nominal Amount</th>
                <th className="px-4 py-3.5">Clearance Prob</th>
                <th className="px-4 py-3.5">Expected Recovery</th>
                <th className="px-4 py-3.5">Priority Tier</th>
                <th className="px-4 py-3.5">Strategy</th>
                <th className="px-4 py-3.5">Guardrails</th>
                <th className="px-4 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-slate-500 text-xs">
                    Calculating recovery priorities...
                  </td>
                </tr>
              ) : filteredOpportunities.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-slate-500 text-xs">
                    No priority opportunities match the current filter.
                  </td>
                </tr>
              ) : (
                filteredOpportunities.map((op) => (
                  <tr
                    key={op.id}
                    onClick={() => onSelectCase(op.id)}
                    className="hover:bg-slate-900/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center font-mono font-bold text-xs ${
                        op.rank === 1 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                        op.rank === 2 ? 'bg-slate-400/20 text-slate-200 border border-slate-400/40' :
                        op.rank === 3 ? 'bg-amber-700/20 text-amber-500 border border-amber-700/40' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        #{op.rank}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="font-bold text-white">{op.customer_name}</div>
                      <div className="text-[11px] font-mono text-blue-400">{op.id}</div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap font-mono font-bold text-slate-200">
                      ₹{op.amount.toLocaleString('en-IN')}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <div className="w-12 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              op.recovery_probability >= 0.75 ? 'bg-emerald-500' :
                              op.recovery_probability >= 0.45 ? 'bg-amber-500' : 'bg-slate-600'
                            }`}
                            style={{ width: `${op.recovery_probability * 100}%` }}
                          />
                        </div>
                        <span className="font-mono text-slate-300">
                          {Math.round(op.recovery_probability * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className="font-mono font-bold text-emerald-400 text-sm">
                        ₹{op.expected_recovery_amount.toLocaleString('en-IN')}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded border ${
                        op.priority_tier === 'HIGH'
                          ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                          : op.priority_tier === 'MEDIUM'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {op.priority_tier}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap font-mono text-[11px] text-purple-300">
                      {op.recommended_strategy}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      {op.guardrail_eligible ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center w-fit gap-1">
                          <ShieldCheck className="w-3 h-3" /> Eligible
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center w-fit gap-1">
                          <ShieldAlert className="w-3 h-3" /> Locked
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCase(op.id);
                        }}
                        className="text-blue-400 hover:text-blue-300 text-xs font-semibold cursor-pointer"
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
