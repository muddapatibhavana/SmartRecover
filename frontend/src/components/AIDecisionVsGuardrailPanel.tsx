import React from 'react';
import { Sparkles, Shield, CheckCircle2, XCircle, AlertTriangle, ArrowRight, Lock, Check } from 'lucide-react';
import { DualDecisionView } from '../types';

interface AIDecisionVsGuardrailPanelProps {
  decision: DualDecisionView;
  onExecute?: () => void;
  executing?: boolean;
}

export const AIDecisionVsGuardrailPanel: React.FC<AIDecisionVsGuardrailPanelProps> = ({
  decision,
  onExecute,
  executing = false
}) => {
  const { ai_decision, guardrail_decision, final_status, final_allowed, summary } = decision;

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl overflow-hidden shadow-2xl">
      {/* Header Banner */}
      <div className="px-6 py-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">Decision Authority Architecture</span>
          <h3 className="text-base font-bold text-white tracking-tight mt-0.5">AI Recommendation vs. Deterministic Guardrails</h3>
        </div>
        <div className="text-right">
          <span className="text-[11px] font-mono text-slate-400">Core Principle:</span>
          <p className="text-xs font-semibold text-slate-200">AI is Advisory • Guardrails are Authoritative</p>
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. AI Decision Column */}
        <div className="rounded-xl bg-slate-900/60 border border-purple-500/20 p-5 relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2 text-purple-400">
                <Sparkles className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">AI Advisory Layer</span>
              </div>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
                Explainable Scoring
              </span>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Recommendation</span>
                <div className="text-xl font-extrabold text-white mt-0.5 flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded-lg text-sm font-bold ${
                    ai_decision.recommended_action === 'RETRY' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                    ai_decision.recommended_action === 'NOTIFY' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                    'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}>
                    {ai_decision.recommended_action}
                  </span>
                  {ai_decision.recommended_delay_hours > 0 && (
                    <span className="text-xs text-slate-400 font-normal">after {ai_decision.recommended_delay_hours}h</span>
                  )}
                </div>
              </div>

              <div className="text-right">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Recovery Score</span>
                <div className="text-2xl font-black text-purple-400 tracking-tight font-mono">
                  {ai_decision.score}<span className="text-xs text-slate-500">/100</span>
                </div>
                <span className="text-[11px] text-slate-400">({Math.round(ai_decision.probability * 100)}% prob)</span>
              </div>
            </div>

            {/* Decision Factors */}
            <div className="mt-5 space-y-2">
              <span className="text-xs font-semibold text-slate-300">Decision Factors:</span>
              <ul className="space-y-1.5">
                {ai_decision.factors.map((factor, i) => (
                  <li key={i} className="text-xs text-slate-400 flex items-start space-x-2">
                    <span className="text-purple-400 mt-0.5">•</span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400">AI Explanation:</span>
            <p className="text-xs text-slate-300 italic mt-1 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
              "{ai_decision.explanation}"
            </p>
          </div>
        </div>

        {/* 2. Guardrail Decision Column */}
        <div className="rounded-xl bg-slate-900/60 border border-blue-500/20 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2 text-blue-400">
                <Shield className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Deterministic Guardrails</span>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                guardrail_decision.allowed
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}>
                STATUS: {guardrail_decision.status}
              </span>
            </div>

            {/* Verified Rules Checklist */}
            <div className="mt-4 space-y-2.5">
              <span className="text-xs font-semibold text-slate-300">Deterministic Safety Invariants:</span>
              <div className="space-y-2">
                {guardrail_decision.rules_checked.map((rule, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start justify-between p-2 rounded-lg text-xs border ${
                      rule.passed
                        ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                        : 'bg-rose-950/20 border-rose-800/40 text-rose-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      {rule.passed ? (
                        <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                      )}
                      <div>
                        <span className="font-medium text-slate-200">{rule.description}</span>
                        {rule.details && (
                          <p className="text-[10px] text-slate-400 mt-0.5">{rule.details}</p>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] font-mono font-bold uppercase">
                      {rule.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Block Reason Warning */}
          {guardrail_decision.blocked_reason && (
            <div className="mt-4 pt-3 border-t border-slate-800">
              <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold">Safety Block Enforced</span>
                  <p className="text-xs text-rose-300 mt-0.5">{guardrail_decision.blocked_reason}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Final Decision Footer Banner */}
      <div className={`px-6 py-4 border-t flex flex-col sm:flex-row items-center justify-between gap-4 ${
        final_allowed
          ? 'bg-emerald-950/30 border-emerald-800/50'
          : 'bg-rose-950/30 border-rose-800/50'
      }`}>
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-full ${final_allowed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
            {final_allowed ? <CheckCircle2 className="w-6 h-6" /> : <Lock className="w-6 h-6" />}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs uppercase font-bold tracking-wider text-slate-400">FINAL DECISION:</span>
              <span className="text-base font-extrabold text-white tracking-tight">{final_status}</span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">{summary}</p>
          </div>
        </div>

        {onExecute && (
          <button
            onClick={onExecute}
            disabled={!final_allowed || executing}
            className={`px-5 py-2.5 rounded-xl font-bold text-xs flex items-center space-x-2 shadow-lg transition-all ${
              final_allowed
                ? 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-emerald-600/30 cursor-pointer'
                : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
            }`}
          >
            <span>{executing ? 'Executing Retry...' : 'Execute Permitted Action'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
