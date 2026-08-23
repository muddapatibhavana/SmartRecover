import React, { useEffect, useState } from 'react';
import { X, Sparkles, Shield, CreditCard, Building2, User, Clock } from 'lucide-react';
import { RecoveryCaseDetail, DualDecisionView, AuditLogEntry } from '../types';
import {
  fetchRecoveryCaseDetail,
  analyzeCase,
  validateAction,
  executeRecoveryAction,
  fetchAuditTrail,
  simulateDispute,
  simulateOptOut
} from '../services/api';
import { AIDecisionVsGuardrailPanel } from './AIDecisionVsGuardrailPanel';
import { AuditTimeline } from './AuditTimeline';

interface CaseDetailModalProps {
  caseId: string | null;
  onClose: () => void;
  onRefreshParent: () => void;
}

export const CaseDetailModal: React.FC<CaseDetailModalProps> = ({
  caseId,
  onClose,
  onRefreshParent
}) => {
  const [caseDetail, setCaseDetail] = useState<RecoveryCaseDetail | null>(null);
  const [dualDecision, setDualDecision] = useState<DualDecisionView | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [executing, setExecuting] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [activeTab, setActiveTab] = useState<'decision' | 'attempts' | 'audit'>('decision');

  const loadAllData = async (id: string) => {
    try {
      setLoading(true);
      const detail = await fetchRecoveryCaseDetail(id);
      setCaseDetail(detail);

      const decision = await validateAction(id);
      setDualDecision(decision);

      const logs = await fetchAuditTrail(id);
      setAuditLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadAllData(caseId);
    }
  }, [caseId]);

  if (!caseId) return null;

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true);
      setActionMessage(null);
      await analyzeCase(caseId);
      await loadAllData(caseId);
      onRefreshParent();
      setActionMessage({ text: 'AI analysis completed and Guardrail check performed!', type: 'success' });
    } catch (err: any) {
      setActionMessage({ text: `Analysis failed: ${err.message}`, type: 'error' });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExecuteRetry = async () => {
    try {
      setExecuting(true);
      setActionMessage(null);
      const res = await executeRecoveryAction(caseId, 'RETRY_PAYMENT');
      await loadAllData(caseId);
      onRefreshParent();
      if (res.success) {
        setActionMessage({ text: res.message, type: 'success' });
      } else {
        setActionMessage({ text: res.message, type: 'error' });
      }
    } catch (err: any) {
      setActionMessage({ text: `Execution failed: ${err.message}`, type: 'error' });
    } finally {
      setExecuting(false);
    }
  };

  const handleInjectDispute = async () => {
    if (!caseDetail) return;
    try {
      setLoading(true);
      await simulateDispute(caseDetail.customer.id, 'Customer filed chargeback dispute on mandate');
      await loadAllData(caseId);
      onRefreshParent();
      setActionMessage({ text: 'Customer dispute recorded! Guardrails immediately halted automation.', type: 'info' });
    } catch (err: any) {
      setActionMessage({ text: err.message, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleInjectOptOut = async () => {
    if (!caseDetail) return;
    try {
      setLoading(true);
      await simulateOptOut(caseDetail.customer.id, 'Customer clicked opt-out in SMS reminder');
      await loadAllData(caseId);
      onRefreshParent();
      setActionMessage({ text: 'Customer opt-out recorded! Workflow safely stopped.', type: 'info' });
    } catch (err: any) {
      setActionMessage({ text: err.message, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div className="bg-[#111827] border border-[#1F2937] w-full max-w-5xl rounded-2xl shadow-2xl overflow-hidden my-auto max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-tight">Recovery Case #{caseId}</h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-slate-800 text-blue-400 border border-slate-700">
                  {caseDetail?.current_status || 'LOADING'}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Customer: <span className="text-slate-200 font-medium">{caseDetail?.customer.name || '...'}</span> • Amount: <span className="text-slate-200 font-mono font-semibold">₹{caseDetail?.amount.toLocaleString('en-IN')}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleAnalyze}
              disabled={analyzing || loading}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white flex items-center space-x-1.5 shadow-md shadow-purple-600/20 transition-all cursor-pointer disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Analyzing...' : 'Run AI Analysis'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Action Status Toast */}
        {actionMessage && (
          <div className={`px-6 py-2 text-xs font-medium flex items-center justify-between border-b ${
            actionMessage.type === 'success' ? 'bg-emerald-950/40 border-emerald-800/40 text-emerald-300' :
            actionMessage.type === 'error' ? 'bg-rose-950/40 border-rose-800/40 text-rose-300' :
            'bg-blue-950/40 border-blue-800/40 text-blue-300'
          }`}>
            <span>{actionMessage.text}</span>
            <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Quick Context Summary Cards */}
          {caseDetail && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  Subscription Plan
                </div>
                <div className="text-xs font-bold text-white mt-1">{caseDetail.subscription.plan_name}</div>
                <div className="text-[11px] font-mono text-slate-400">₹{caseDetail.amount.toLocaleString('en-IN')} / {caseDetail.subscription.interval}</div>
              </div>

              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <CreditCard className="w-3.5 h-3.5 text-slate-400" />
                  Mandate & Bank
                </div>
                <div className="text-xs font-bold text-white mt-1">{caseDetail.mandate.mandate_type}</div>
                <div className="text-[11px] text-slate-400">{caseDetail.mandate.bank_name}</div>
              </div>

              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  Customer Reliability
                </div>
                <div className="text-xs font-bold text-white mt-1">
                  {caseDetail.customer.historical_success_count} Successes / {caseDetail.customer.historical_failure_count} Fails
                </div>
                <div className="text-[11px] text-slate-400">
                  {caseDetail.customer.has_dispute ? '⚠️ Active Dispute' : caseDetail.customer.is_opted_out ? '⚠️ Opted Out' : '✓ Clean Account'}
                </div>
              </div>

              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  Failure Information
                </div>
                <div className="text-xs font-bold text-rose-400 mt-1 truncate">{caseDetail.failure_code}</div>
                <div className="text-[11px] text-slate-400 truncate">{caseDetail.failure_reason}</div>
              </div>
            </div>
          )}

          {/* Navigation Tabs inside modal */}
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab('decision')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'decision'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              AI & Guardrail Decisions
            </button>
            <button
              onClick={() => setActiveTab('attempts')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'attempts'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Payment Attempts ({caseDetail?.payment_attempts.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'audit'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Audit Trail ({auditLogs.length})
            </button>
          </div>

          {/* Tab 1: AI vs Guardrail Panel */}
          {activeTab === 'decision' && dualDecision && (
            <div className="space-y-4">
              <AIDecisionVsGuardrailPanel
                decision={dualDecision}
                onExecute={handleExecuteRetry}
                executing={executing}
              />

              {/* Simulation Testing Bar */}
              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-slate-300">Simulate Safety Scenarios on this Case:</span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={handleInjectDispute}
                    className="px-2.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-medium transition-all"
                  >
                    + Inject Dispute
                  </button>
                  <button
                    onClick={handleInjectOptOut}
                    className="px-2.5 py-1 rounded bg-orange-500/10 hover:bg-orange-500/20 text-orange-300 border border-orange-500/30 text-xs font-medium transition-all"
                  >
                    + Inject Opt-Out
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Payment Attempts History */}
          {activeTab === 'attempts' && caseDetail && (
            <div className="bg-slate-900/60 rounded-xl border border-slate-800 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-400 font-semibold border-b border-slate-700">
                  <tr>
                    <th className="px-4 py-3">Attempt #</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Failure Reason</th>
                    <th className="px-4 py-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {caseDetail.payment_attempts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                        No retry attempts executed yet in this recovery cycle.
                      </td>
                    </tr>
                  ) : (
                    caseDetail.payment_attempts.map((att) => (
                      <tr key={att.id}>
                        <td className="px-4 py-3 font-mono font-bold text-white">Attempt #{att.attempt_number}</td>
                        <td className="px-4 py-3 font-mono">₹{att.amount.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            att.status === 'SUCCESS' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                            'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}>
                            {att.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-400">{att.failure_reason || '—'}</td>
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                          {new Date(att.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 3: Live Audit Timeline */}
          {activeTab === 'audit' && (
            <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800">
              <AuditTimeline logs={auditLogs} loading={loading} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
