import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ArrowUpRight,
  MessageSquare,
  ShieldAlert,
  FileText,
  Sparkles,
  UserX,
  ExternalLink,
  Info,
  Check
} from 'lucide-react';
import { HumanReviewItem } from '../types';
import { updateHumanReview } from '../services/api';

interface HumanReviewQueueProps {
  reviews: HumanReviewItem[];
  loading: boolean;
  onRefresh: () => void;
  onSelectCase: (caseId: string) => void;
}

export const HumanReviewQueue: React.FC<HumanReviewQueueProps> = ({
  reviews,
  loading,
  onRefresh,
  onSelectCase
}) => {
  const [selectedReview, setSelectedReview] = useState<HumanReviewItem | null>(null);
  const [actionNotes, setActionNotes] = useState<string>('');
  const [resolutionAction, setResolutionAction] = useState<string>('RESOLVED_CUSTOMER_CONTACTED');
  const [escalationAction, setEscalationAction] = useState<string>('ESCALATED_FINANCE_OPERATIONS');
  const [updating, setUpdating] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');

  const handleAction = async (action: 'review' | 'resolve' | 'escalate', targetReview?: HumanReviewItem) => {
    const item = targetReview || selectedReview;
    if (!item) return;

    try {
      setUpdating(true);
      const actionPayload = action === 'resolve' ? resolutionAction : action === 'escalate' ? escalationAction : undefined;
      await updateHumanReview(item.id, action, actionNotes, actionPayload);
      setSelectedReview(null);
      setActionNotes('');
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setUpdating(false);
    }
  };

  const filteredReviews = reviews.filter((r) => {
    if (statusFilter === 'ALL') return true;
    return r.status === statusFilter;
  });

  const getStopReasonLabel = (reason?: string) => {
    if (!reason) return 'Human Review Triggered';
    switch (reason) {
      case 'CUSTOMER_DISPUTED':
        return 'Customer Dispute Detected';
      case 'CUSTOMER_OPTED_OUT':
        return 'Customer Opted-Out';
      case 'MAX_ATTEMPTS_REACHED':
        return 'Max Retries (2) Exceeded';
      case 'RECOVERY_WINDOW_EXPIRED':
        return '7-Day Window Expired';
      case 'HUMAN_REVIEW_REQUIRED':
        return 'Low AI Score (<40%) / Inactive';
      default:
        return reason;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Human Review & Intervention Queue</h2>
            <p className="text-xs text-slate-400">Review flagged mandates, resolve disputes, and escalate critical payment issues with immutable audit records</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {['PENDING', 'REVIEWED', 'RESOLVED', 'ESCALATED', 'ALL'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                statusFilter === st
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Review Queue Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left List: Review Cards */}
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <div className="p-12 text-center text-slate-500 text-xs bg-[#111827] rounded-xl border border-slate-800">
              Loading review queue...
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs bg-[#111827] rounded-xl border border-slate-800">
              No items found in {statusFilter} review queue.
            </div>
          ) : (
            filteredReviews.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedReview(r)}
                className={`p-4 rounded-xl border transition-all cursor-pointer bg-[#111827] hover:border-blue-500/50 space-y-3 ${
                  selectedReview?.id === r.id ? 'border-blue-500 ring-1 ring-blue-500/50 bg-slate-900/80' : 'border-[#1F2937]'
                }`}
              >
                {/* Header line: Case ID, Customer, Amount, Status */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-blue-400">Case #{r.recovery_case_id}</span>
                    <span className="text-xs font-semibold text-white">• {r.customer.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-slate-200">
                      ₹{r.case_amount.toLocaleString('en-IN')}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      r.status === 'PENDING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                      r.status === 'REVIEWED' ? 'bg-blue-500/10 text-blue-400 border-blue-500/30' :
                      r.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                      'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    }`}>
                      {r.status}
                    </span>
                  </div>
                </div>

                {/* Reason & Failure Context */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-start space-x-2">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] font-semibold uppercase text-slate-500">Trigger Reason:</span>
                      <p className="text-xs text-rose-300 font-medium">{r.trigger_reason}</p>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-start space-x-2">
                    <UserX className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] font-semibold uppercase text-slate-500">Why Automation Stopped:</span>
                      <p className="text-xs text-amber-300 font-medium">{getStopReasonLabel(r.stop_reason)}</p>
                    </div>
                  </div>
                </div>

                {/* AI Recommendation & Decision Pill */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60 text-xs">
                  <div className="flex items-center space-x-3 text-slate-400">
                    <div className="flex items-center space-x-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                      <span className="text-[11px]">AI Rec:</span>
                      <span className="font-semibold text-purple-300">{r.ai_recommendation || 'HUMAN_REVIEW'}</span>
                      {r.ai_score !== undefined && r.ai_score !== null && (
                        <span className="font-mono text-[10px] text-slate-500">({Math.round(r.ai_score)}%)</span>
                      )}
                    </div>
                  </div>

                  {/* Actions Bar on card */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(r.recovery_case_id);
                      }}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 text-[11px] font-semibold flex items-center space-x-1 border border-slate-700 transition-colors cursor-pointer"
                      title="Review full case details and dual AI/Guardrail panel"
                    >
                      <span>Review Details</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>

                    {r.status === 'PENDING' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedReview(r);
                          handleAction('review', r);
                        }}
                        disabled={updating}
                        className="px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-[11px] font-semibold border border-blue-500/30 transition-colors cursor-pointer"
                      >
                        Mark In-Review
                      </button>
                    )}

                    {r.status !== 'RESOLVED' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedReview(r);
                          handleAction('resolve', r);
                        }}
                        disabled={updating}
                        className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold flex items-center space-x-1 shadow-sm transition-colors cursor-pointer"
                      >
                        <Check className="w-3 h-3" />
                        <span>Resolve</span>
                      </button>
                    )}

                    {r.status !== 'ESCALATED' && r.status !== 'RESOLVED' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedReview(r);
                          handleAction('escalate', r);
                        }}
                        disabled={updating}
                        className="px-2.5 py-1 rounded bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 text-[11px] font-semibold border border-rose-500/30 flex items-center space-x-1 transition-colors cursor-pointer"
                      >
                        <ArrowUpRight className="w-3 h-3" />
                        <span>Escalate</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Action Console */}
        <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 shadow-xl h-fit space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <FileText className="w-4 h-4 text-blue-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Human Operator Console</h3>
          </div>

          {selectedReview ? (
            <div className="space-y-4">
              <div>
                <span className="text-[11px] text-slate-500 uppercase font-semibold">Active Review Target:</span>
                <div className="text-sm font-bold text-white mt-0.5">{selectedReview.customer.name}</div>
                <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                  <span className="font-mono text-blue-400">#{selectedReview.recovery_case_id}</span> •
                  <span className="font-mono text-slate-200">₹{selectedReview.case_amount.toLocaleString('en-IN')}</span>
                </div>
              </div>

              {/* Review summary box */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs">
                <div>
                  <span className="font-semibold text-amber-400">Trigger Reason:</span>
                  <p className="text-slate-300 mt-0.5">{selectedReview.trigger_reason}</p>
                </div>
                <div className="pt-2 border-t border-slate-800/80">
                  <span className="font-semibold text-slate-400">Why Automation Stopped:</span>
                  <p className="text-slate-300 mt-0.5">{getStopReasonLabel(selectedReview.stop_reason)}</p>
                </div>
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-slate-400">AI Advisory:</span>
                  <span className="font-semibold text-purple-400">{selectedReview.ai_recommendation || 'HUMAN_REVIEW'}</span>
                </div>
              </div>

              {/* Resolution Action Picker */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Resolution Strategy:
                </label>
                <select
                  value={resolutionAction}
                  onChange={(e) => setResolutionAction(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="RESOLVED_CUSTOMER_CONTACTED">Customer Contacted & Bank Details Updated</option>
                  <option value="RESOLVED_MANUAL_RETRY_SCHEDULED">Manual Mandate Debit Scheduled</option>
                  <option value="RESOLVED_SUBSCRIPTION_CANCELLED">Subscription Cancelled per Customer Request</option>
                  <option value="RESOLVED_DISPUTE_SETTLED">Dispute Settled & Invoice Re-issued</option>
                  <option value="RESOLVED_WAIVED_OFF">Payment Waived / Written Off</option>
                </select>
              </div>

              {/* Escalation Action Picker */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Escalation Target:
                </label>
                <select
                  value={escalationAction}
                  onChange={(e) => setEscalationAction(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="ESCALATED_FINANCE_OPERATIONS">Finance & Collections Operations</option>
                  <option value="ESCALATED_LEGAL_COMPLIANCE">Legal & Compliance Team</option>
                  <option value="ESCALATED_ACCOUNT_EXECUTIVE">Strategic Account Executive</option>
                </select>
              </div>

              {/* Operator Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Operator Investigation Notes:
                </label>
                <textarea
                  rows={3}
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder="e.g. Spoke with account billing POC; verified dispute reason and updated recovery plan..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => handleAction('resolve')}
                  disabled={updating}
                  className="w-full py-2.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/20 transition-all cursor-pointer disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Mark Resolved (Safe Stop)</span>
                </button>

                <button
                  onClick={() => handleAction('review')}
                  disabled={updating}
                  className="w-full py-2 px-3 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>Mark In-Review</span>
                </button>

                <button
                  onClick={() => handleAction('escalate')}
                  disabled={updating}
                  className="w-full py-2 px-3 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 font-semibold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
                >
                  <ArrowUpRight className="w-4 h-4" />
                  <span>Escalate Target</span>
                </button>

                <button
                  onClick={() => onSelectCase(selectedReview.recovery_case_id)}
                  className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs flex items-center justify-center space-x-1.5 transition-all cursor-pointer"
                >
                  <span>Open Full Case Screen</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs space-y-2">
              <Info className="w-8 h-8 mx-auto text-slate-600" />
              <p>Select any case from the queue to view trigger details, log operator notes, and take Resolve or Escalate actions.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
