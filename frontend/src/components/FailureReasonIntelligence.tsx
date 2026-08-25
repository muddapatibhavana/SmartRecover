import React, { useState, useEffect } from 'react';
import { Brain, Activity } from 'lucide-react';
import { FailureClassificationDetail } from '../types';
import { fetchFailureCatalog } from '../services/api';

export const FailureReasonIntelligence: React.FC = () => {
  const [catalog, setCatalog] = useState<FailureClassificationDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedFailure, setSelectedFailure] = useState<FailureClassificationDetail | null>(null);

  useEffect(() => {
    async function loadCatalog() {
      try {
        setLoading(true);
        const data = await fetchFailureCatalog();
        setCatalog(data);
        if (data.length > 0) setSelectedFailure(data[0]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadCatalog();
  }, []);

  const categories = ['ALL', 'INFRASTRUCTURE', 'CUSTOMER_FINANCIAL', 'MANDATE_LIFECYCLE', 'CREDENTIAL', 'DISPUTE_FRAUD', 'CYCLE_LIMIT'];

  const filteredCatalog = catalog.filter((f) => {
    if (selectedCategory === 'ALL') return true;
    return f.category === selectedCategory;
  });

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'LOW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">LOW RISK</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">MEDIUM RISK</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/10 text-orange-400 border border-orange-500/30">HIGH RISK</span>;
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">CRITICAL</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">{risk}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Failure-Reason Intelligence</h2>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Taxonomy & Strategy Mapping
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Categorizes recurring mandate failure telemetry into risk tiers, retry suitability, and customer communication guidelines.
            </p>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap items-center gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Catalog Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left List of Failure Types */}
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-500 bg-[#111827] rounded-xl border border-slate-800">
              Loading failure intelligence catalog...
            </div>
          ) : (
            filteredCatalog.map((item) => (
              <div
                key={item.code}
                onClick={() => setSelectedFailure(item)}
                className={`p-4 rounded-xl border transition-all cursor-pointer bg-[#111827] hover:border-blue-500/50 space-y-3 ${
                  selectedFailure?.code === item.code ? 'border-blue-500 ring-1 ring-blue-500/50 bg-slate-900/80' : 'border-[#1F2937]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-blue-400">{item.code}</span>
                    <span className="text-xs font-semibold text-white">• {item.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getRiskBadge(item.risk_level)}
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      item.retry_suitable
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    }`}>
                      Retry: {item.retry_suitable ? 'YES' : 'NO'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-400">{item.description}</p>

                <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px]">
                  <div className="flex items-center space-x-2 text-slate-400">
                    <span>Preferred Strategy:</span>
                    <span className="font-semibold text-purple-300 font-mono">{item.preferred_strategy}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-slate-400">
                    <span>Historical Recovery:</span>
                    <span className="font-bold text-emerald-400">{Math.round(item.historical_recovery_rate * 100)}%</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Detail Panel: "Why this strategy?" */}
        <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 shadow-xl h-fit space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Activity className="w-4 h-4 text-purple-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Strategy & Communication Matrix</h3>
          </div>

          {selectedFailure ? (
            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Selected Failure Pattern:</span>
                <div className="text-sm font-bold text-white mt-0.5">{selectedFailure.name}</div>
                <div className="font-mono text-[11px] text-blue-400 mt-0.5">{selectedFailure.code}</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-bold text-purple-400">Why this strategy?</span>
                <p className="text-slate-300 leading-relaxed">{selectedFailure.explanation_template}</p>
              </div>

              <div className="space-y-2.5">
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1">
                  <span className="font-semibold text-slate-400">Recommended Retry Cooldown:</span>
                  <div className="font-mono font-bold text-white">
                    {selectedFailure.recommended_delay_hours > 0
                      ? `${selectedFailure.recommended_delay_hours} Hours`
                      : 'No automated retry (Immediate Action / Lock)'}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1">
                  <span className="font-semibold text-slate-400">Customer Communication Guidance:</span>
                  <p className="text-slate-300 leading-relaxed">{selectedFailure.communication_recommendation}</p>
                </div>

                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1">
                  <span className="font-semibold text-slate-400">Human Review Policy:</span>
                  <div className={`font-bold ${selectedFailure.human_review_required ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {selectedFailure.human_review_required ? 'Escalate to Operator Review' : 'Automated Recovery Eligible'}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-slate-500">
              Select a failure category from the list to view strategy details and communication guidance.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
