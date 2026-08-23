import React, { useState } from 'react';
import { PlayCircle, AlertOctagon, ShieldAlert, UserX } from 'lucide-react';
import {
  simulatePaymentFailure,
  simulateDispute,
  simulateOptOut
} from '../services/api';

interface PaymentSimulatorControlsProps {
  onSimulationComplete: () => void;
}

export const PaymentSimulatorControls: React.FC<PaymentSimulatorControlsProps> = ({
  onSimulationComplete
}) => {
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('CUST-1001');
  const [simulating, setSimulating] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<{ message: string; type: 'success' | 'warning' | 'info' } | null>(null);

  const demoCustomers = [
    { id: 'CUST-1001', name: 'ABC Technologies (Customer A - High Reliability)' },
    { id: 'CUST-1002', name: 'BlueWave Dynamics (Customer B - Low Score)' },
    { id: 'CUST-1003', name: 'Apex Retail Logistics (Customer C - Dispute Ready)' },
    { id: 'CUST-1004', name: 'CloudScale Analytics (Customer D - Recovery Journey)' },
    { id: 'CUST-1005', name: 'Horizon Media Labs (Customer E - Max Attempts)' },
    { id: 'CUST-1006', name: 'FinPulse Systems (Customer F - Opt-Out Ready)' },
  ];

  const handleSimulateFailure = async () => {
    try {
      setSimulating(true);
      const res = await simulatePaymentFailure(
        selectedCustomerId,
        14999.0,
        'BANK_NETWORK_TIMEOUT',
        'Simulated recurring mandate debit failure via NPCI switch timeout'
      );
      setLastResult({ message: res.message, type: 'info' });
      onSimulationComplete();
    } catch (err: any) {
      setLastResult({ message: err.message, type: 'warning' });
    } finally {
      setSimulating(false);
    }
  };

  const handleSimulateDispute = async () => {
    try {
      setSimulating(true);
      const res = await simulateDispute(
        selectedCustomerId,
        'Customer contested mandate recurring charge with issuing bank'
      );
      setLastResult({ message: res.message, type: 'warning' });
      onSimulationComplete();
    } catch (err: any) {
      setLastResult({ message: err.message, type: 'warning' });
    } finally {
      setSimulating(false);
    }
  };

  const handleSimulateOptOut = async () => {
    try {
      setSimulating(true);
      const res = await simulateOptOut(
        selectedCustomerId,
        'Customer clicked cancel recurring mandate via SMS prompt'
      );
      setLastResult({ message: res.message, type: 'warning' });
      onSimulationComplete();
    } catch (err: any) {
      setLastResult({ message: err.message, type: 'warning' });
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <PlayCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">Payment & Event Simulator</h3>
            <p className="text-xs text-slate-400">Safely test recurring mandate failures, disputes, and opt-outs without real payment credentials</p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-900 text-emerald-400 border border-slate-800">
          Sandbox Mode: Active
        </span>
      </div>

      {/* Customer Target Selector */}
      <div className="max-w-md">
        <label className="block text-xs font-semibold text-slate-300 mb-1.5">
          Select Target Customer:
        </label>
        <select
          value={selectedCustomerId}
          onChange={(e) => setSelectedCustomerId(e.target.value)}
          className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
        >
          {demoCustomers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Simulator Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-rose-400">
              <AlertOctagon className="w-4 h-4" />
              <span className="text-xs font-bold uppercase">1. Mandate Failure</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Trigger a simulated debit failure (e.g. temporary timeout or insufficient funds).
            </p>
          </div>
          <button
            onClick={handleSimulateFailure}
            disabled={simulating}
            className="w-full py-2 px-3 rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white font-bold text-xs shadow-md shadow-rose-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            Simulate Payment Failure
          </button>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-amber-400">
              <ShieldAlert className="w-4 h-4" />
              <span className="text-xs font-bold uppercase">2. Customer Dispute</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Simulate customer disputing the mandate charge. Guardrails will immediately block automated retries.
            </p>
          </div>
          <button
            onClick={handleSimulateDispute}
            disabled={simulating}
            className="w-full py-2 px-3 rounded-lg bg-amber-600/80 hover:bg-amber-600 text-white font-bold text-xs shadow-md shadow-amber-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            Simulate Customer Dispute
          </button>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-orange-400">
              <UserX className="w-4 h-4" />
              <span className="text-xs font-bold uppercase">3. Customer Opt-Out</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Simulate customer requesting opt-out. Workflow will automatically transition to STOPPED.
            </p>
          </div>
          <button
            onClick={handleSimulateOptOut}
            disabled={simulating}
            className="w-full py-2 px-3 rounded-lg bg-orange-600/80 hover:bg-orange-600 text-white font-bold text-xs shadow-md shadow-orange-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            Simulate Customer Opt-Out
          </button>
        </div>
      </div>

      {/* Last Result Box */}
      {lastResult && (
        <div className={`p-3.5 rounded-lg border text-xs font-mono ${
          lastResult.type === 'success' ? 'bg-emerald-950/40 border-emerald-800/40 text-emerald-300' :
          lastResult.type === 'warning' ? 'bg-amber-950/40 border-amber-800/40 text-amber-300' :
          'bg-blue-950/40 border-blue-800/40 text-blue-300'
        }`}>
          {lastResult.message}
        </div>
      )}
    </div>
  );
};
