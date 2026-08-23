import React from 'react';
import { Search, Sparkles, Shield, ArrowRight, CheckCircle, AlertOctagon, UserX, FileText } from 'lucide-react';
import { RecoveryCaseSummary } from '../types';

interface RecoveryCaseTableProps {
  cases: RecoveryCaseSummary[];
  loading: boolean;
  onSelectCase: (caseId: string) => void;
  selectedStatus: string;
  setSelectedStatus: (status: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

export const RecoveryCaseTable: React.FC<RecoveryCaseTableProps> = ({
  cases,
  loading,
  onSelectCase,
  selectedStatus,
  setSelectedStatus,
  searchQuery,
  setSearchQuery
}) => {
  const statusFilters = [
    { id: 'ALL', label: 'All Cases' },
    { id: 'FAILED', label: 'Failed' },
    { id: 'ACTION_ALLOWED', label: 'Retry Allowed' },
    { id: 'ACTION_BLOCKED', label: 'Blocked' },
    { id: 'RECOVERED', label: 'Recovered' },
    { id: 'HUMAN_REVIEW', label: 'Human Review' },
    { id: 'STOPPED', label: 'Stopped' }
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RECOVERED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Recovered</span>;
      case 'ACTION_ALLOWED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1"><Shield className="w-3 h-3" /> Retry Allowed</span>;
      case 'ACTION_BLOCKED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1"><AlertOctagon className="w-3 h-3" /> Blocked</span>;
      case 'HUMAN_REVIEW':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1"><FileText className="w-3 h-3" /> Human Review</span>;
      case 'STOPPED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-700/50 text-slate-300 border border-slate-600 flex items-center gap-1"><UserX className="w-3 h-3" /> Stopped</span>;
      case 'AI_RECOMMENDED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1"><Sparkles className="w-3 h-3" /> AI Recommended</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">{status}</span>;
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl shadow-xl overflow-hidden">
      {/* Search & Filter Header */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by customer, case ID, reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {statusFilters.map((f) => (
            <button
              key={f.id}
              onClick={() => setSelectedStatus(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedStatus === f.id
                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800/80'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Cases Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 text-[11px]">
            <tr>
              <th className="px-5 py-3.5">Case ID</th>
              <th className="px-5 py-3.5">Customer</th>
              <th className="px-5 py-3.5">Amount</th>
              <th className="px-5 py-3.5">Failure Reason</th>
              <th className="px-5 py-3.5">Recovery Score</th>
              <th className="px-5 py-3.5">AI Rec</th>
              <th className="px-5 py-3.5">Guardrails</th>
              <th className="px-5 py-3.5">Current Status</th>
              <th className="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {loading ? (
              <tr>
                <td colSpan={9} className="px-5 py-12 text-center text-slate-500">
                  Loading recovery cases...
                </td>
              </tr>
            ) : cases.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-5 py-12 text-center text-slate-500">
                  No recovery cases match your search criteria.
                </td>
              </tr>
            ) : (
              cases.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => onSelectCase(c.id)}
                  className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                >
                  <td className="px-5 py-3.5 font-mono font-bold text-blue-400 whitespace-nowrap">
                    #{c.id}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="font-semibold text-white">{c.customer_name}</div>
                    <div className="text-[11px] text-slate-500 truncate max-w-[160px]">{c.customer_email}</div>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap font-mono font-semibold text-slate-200">
                    ₹{c.amount.toLocaleString('en-IN')}
                  </td>
                  <td className="px-5 py-3.5 max-w-xs">
                    <div className="truncate text-slate-300">{c.failure_reason}</div>
                    <div className="text-[10px] text-slate-500 font-mono">Attempts: {c.attempt_count}/2</div>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    {c.recovery_score !== undefined && c.recovery_score !== null ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full ${
                              c.recovery_score >= 80 ? 'bg-emerald-500' :
                              c.recovery_score >= 60 ? 'bg-blue-500' :
                              c.recovery_score >= 40 ? 'bg-amber-500' : 'bg-rose-500'
                            }`}
                            style={{ width: `${c.recovery_score}%` }}
                          />
                        </div>
                        <span className="font-mono font-bold text-slate-200">{Math.round(c.recovery_score)}%</span>
                      </div>
                    ) : (
                      <span className="text-slate-500 text-[11px] italic">Not analyzed</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    {c.ai_recommendation ? (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        c.ai_recommendation === 'RETRY' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                        c.ai_recommendation === 'NOTIFY' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                        'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                        {c.ai_recommendation}
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[11px]">—</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      c.guardrail_status === 'ALLOWED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                      c.guardrail_status === 'BLOCKED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                      'bg-slate-800 text-slate-400 border-slate-700'
                    }`}>
                      {c.guardrail_status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    {getStatusBadge(c.current_status)}
                  </td>
                  <td className="px-5 py-3.5 text-right whitespace-nowrap">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(c.id);
                      }}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white transition-colors text-xs font-semibold"
                    >
                      <span>Inspect</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
