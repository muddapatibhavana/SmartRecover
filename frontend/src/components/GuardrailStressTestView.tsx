import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  Sparkles,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { StressTestScenario, StressTestResult, StressTestRunRequest } from '../types';
import { fetchStressTestScenarios, runStressTest } from '../services/api';

export const GuardrailStressTestView: React.FC = () => {
  const [scenarios, setScenarios] = useState<StressTestScenario[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<string>('STRESS-DISPUTE-01');
  const [testResult, setTestResult] = useState<StressTestResult | null>(null);
  const [running, setRunning] = useState<boolean>(false);

  // Custom Sandbox Toggles
  const [customAction, setCustomAction] = useState<string>('RETRY_NOW');
  const [disputeToggle, setDisputeToggle] = useState<boolean>(true);
  const [maxRetriesToggle, setMaxRetriesToggle] = useState<boolean>(false);
  const [optOutToggle, setOptOutToggle] = useState<boolean>(false);
  const [highRiskToggle, setHighRiskToggle] = useState<boolean>(false);
  const [stoppedToggle, setStoppedToggle] = useState<boolean>(false);

  useEffect(() => {
    async function loadScenarios() {
      try {
        const data = await fetchStressTestScenarios();
        setScenarios(data);
        if (data.length > 0) {
          executePredefinedTest(data[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    }
    loadScenarios();
  }, []);

  const executePredefinedTest = async (scenarioId: string) => {
    try {
      setRunning(true);
      setActiveScenarioId(scenarioId);
      const res = await runStressTest({ scenario_id: scenarioId });
      setTestResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  const executeCustomTest = async () => {
    try {
      setRunning(true);
      setActiveScenarioId('CUSTOM');
      const payload: StressTestRunRequest = {
        proposed_action: customAction,
        simulate_dispute: disputeToggle,
        simulate_max_retries: maxRetriesToggle,
        simulate_opt_out: optOutToggle,
        simulate_high_risk: highRiskToggle,
        simulate_stopped: stoppedToggle
      };
      const res = await runStressTest(payload);
      setTestResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-rose-950/40 via-slate-900 to-purple-950/30 border border-rose-900/40 rounded-xl p-6 shadow-xl space-y-3">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-black text-white tracking-tight">AI Safety & Guardrail Stress-Test Mode</h2>
              <span className="text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                Adversarial Verification
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Intentionally generates aggressive AI recommendations to prove deterministic GuardrailEngine safety enforcement.
            </p>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono flex items-center justify-between">
          <span className="text-slate-400">Core Invariant:</span>
          <span className="text-rose-400 font-bold">
            "AI RECOMMENDS. DETERMINISTIC GUARDRAILS DECIDE. ZERO PAYMENT EXECUTION."
          </span>
        </div>
      </div>

      {/* Predefined Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {scenarios.map((sc) => {
          const isSelected = activeScenarioId === sc.id;
          const isBlocked = sc.expected_guardrail_result === 'BLOCKED';

          return (
            <button
              key={sc.id}
              onClick={() => executePredefinedTest(sc.id)}
              disabled={running}
              className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between space-y-2 ${
                isSelected
                  ? 'border-rose-500 ring-1 ring-rose-500/50 bg-slate-900 shadow-lg'
                  : 'border-[#1F2937] bg-[#111827] hover:border-slate-700'
              }`}
            >
              <div>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                  isBlocked ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                }`}>
                  {sc.expected_guardrail_result}
                </span>
                <h4 className="text-xs font-bold text-white mt-1.5 line-clamp-2">{sc.name}</h4>
              </div>

              <div className="text-[11px] text-slate-400 font-mono pt-2 border-t border-slate-800">
                AI: <span className="text-purple-300 font-bold">{sc.proposed_ai_recommendation}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Hero Visual Flow Display */}
      {testResult && (
        <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-500">Live Stress Verification Verdict:</span>
              <h3 className="text-base font-bold text-white mt-0.5">{testResult.scenario_name}</h3>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-slate-900 text-amber-400 border border-slate-800">
              {testResult.simulation_badge}
            </span>
          </div>

          {/* Visual Block Architecture */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            {/* Step 1: AI Proposal */}
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-800/40 space-y-2">
              <div className="flex items-center space-x-1.5 text-purple-400 text-xs font-bold uppercase">
                <Sparkles className="w-4 h-4" />
                <span>1. Aggressive AI Action</span>
              </div>
              <div className="text-lg font-mono font-extrabold text-white">
                {testResult.ai_proposed_action}
              </div>
              <p className="text-[11px] text-purple-300/80">
                AI advisory recommendation generated without policy filtering.
              </p>
            </div>

            {/* Step 2: Guardrail Engine Decision */}
            <div className={`p-4 rounded-xl border space-y-2 ${
              testResult.guardrail_allowed
                ? 'bg-emerald-950/20 border-emerald-800/40'
                : 'bg-rose-950/30 border-rose-800/50'
            }`}>
              <div className="flex items-center space-x-1.5 text-xs font-bold uppercase">
                {testResult.guardrail_allowed ? (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-400">2. Guardrail Engine Result</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <span className="text-rose-400">2. Guardrail Engine Result</span>
                  </>
                )}
              </div>
              <div className={`text-xl font-extrabold font-mono flex items-center gap-2 ${
                testResult.guardrail_allowed ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {testResult.guardrail_allowed ? '✅ ALLOWED' : '❌ BLOCKED'}
              </div>
              <p className="text-[11px] text-slate-300">
                {testResult.guardrail_blocked_reason || 'All 10 deterministic safety invariants passed.'}
              </p>
            </div>

            {/* Step 3: Key Takeaway */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <span className="text-[10px] uppercase font-bold text-slate-400">3. Safety Assurance</span>
              <div className="text-xs font-bold text-white leading-relaxed">
                {testResult.guardrail_allowed
                  ? "Safe for execution. Verified across 10 deterministic fintech invariants."
                  : "AI wanted to retry. The safety system refused."}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                Real Payment Execution: <span className="text-emerald-400 font-bold">PREVENTED (100% Zero-Touch)</span>
              </div>
            </div>
          </div>

          {/* Detailed Rule Invariants Table */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-bold text-white uppercase tracking-wider">Guardrail Invariant Verifications:</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {testResult.rules_checked.map((rule, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border flex items-center justify-between text-xs ${
                    rule.passed
                      ? 'bg-slate-900/60 border-slate-800 text-slate-300'
                      : 'bg-rose-950/20 border-rose-800/40 text-rose-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    {rule.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    )}
                    <div>
                      <div className="font-semibold text-white">{rule.description}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{rule.rule_name}</div>
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold font-mono ${rule.passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {rule.passed ? 'PASS' : 'FAIL'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Custom Stress-Test Runner */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
          <Zap className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Custom Adversarial Simulation Sandbox</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Select Unsafe AI Recommendation:
            </label>
            <select
              value={customAction}
              onChange={(e) => setCustomAction(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500 font-mono"
            >
              <option value="RETRY_NOW">RETRY_NOW (Immediate Debit Attempt)</option>
              <option value="RETRY_AFTER_6H">RETRY_AFTER_6H (Short Cooldown)</option>
              <option value="RETRY_AFTER_24H">RETRY_AFTER_24H (Standard Retry)</option>
              <option value="STOP_RECOVERY">STOP_RECOVERY (Halt Automation)</option>
            </select>
          </div>

          <div className="md:col-span-2 space-y-2">
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Simulate Dangerous / Adversarial Account States:
            </label>
            <div className="flex flex-wrap gap-2">
              <label className={`px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all flex items-center space-x-1.5 ${
                disputeToggle ? 'bg-rose-500/20 border-rose-500/40 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                <input
                  type="checkbox"
                  checked={disputeToggle}
                  onChange={(e) => setDisputeToggle(e.target.checked)}
                  className="hidden"
                />
                <span>🔥 Active Customer Dispute</span>
              </label>

              <label className={`px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all flex items-center space-x-1.5 ${
                maxRetriesToggle ? 'bg-rose-500/20 border-rose-500/40 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                <input
                  type="checkbox"
                  checked={maxRetriesToggle}
                  onChange={(e) => setMaxRetriesToggle(e.target.checked)}
                  className="hidden"
                />
                <span>⚠️ Max 2 Retries Exceeded</span>
              </label>

              <label className={`px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all flex items-center space-x-1.5 ${
                optOutToggle ? 'bg-rose-500/20 border-rose-500/40 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                <input
                  type="checkbox"
                  checked={optOutToggle}
                  onChange={(e) => setOptOutToggle(e.target.checked)}
                  className="hidden"
                />
                <span>🛑 Customer Opted Out</span>
              </label>

              <label className={`px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all flex items-center space-x-1.5 ${
                highRiskToggle ? 'bg-rose-500/20 border-rose-500/40 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                <input
                  type="checkbox"
                  checked={highRiskToggle}
                  onChange={(e) => setHighRiskToggle(e.target.checked)}
                  className="hidden"
                />
                <span>🛡️ High Risk / Fraud Signal</span>
              </label>

              <label className={`px-3 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer transition-all flex items-center space-x-1.5 ${
                stoppedToggle ? 'bg-rose-500/20 border-rose-500/40 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                <input
                  type="checkbox"
                  checked={stoppedToggle}
                  onChange={(e) => setStoppedToggle(e.target.checked)}
                  className="hidden"
                />
                <span>⛔ Case in STOPPED State</span>
              </label>
            </div>
          </div>
        </div>

        <button
          onClick={executeCustomTest}
          disabled={running}
          className="w-full py-2.5 px-4 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg shadow-rose-600/20 transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          <ShieldAlert className="w-4 h-4" />
          <span>{running ? 'Evaluating Invariants...' : 'Run Custom Stress Verification'}</span>
        </button>
      </div>
    </div>
  );
};
