import React from 'react';
import { ShieldCheck, AlertTriangle, UserX, Clock, CheckCircle, HelpCircle, FileText } from 'lucide-react';
import { StopReasonCount } from '../types';

interface StopReasonAnalyticsProps {
  breakdown: StopReasonCount[];
}

export const StopReasonAnalytics: React.FC<StopReasonAnalyticsProps> = ({ breakdown }) => {
  const getReasonConfig = (reason: string) => {
    switch (reason) {
      case 'PAYMENT_RECOVERED':
        return {
          icon: CheckCircle,
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/20',
          barColor: 'bg-emerald-500',
          desc: 'Workflow stopped automatically because payment was successfully recovered.'
        };
      case 'MAX_ATTEMPTS_REACHED':
        return {
          icon: AlertTriangle,
          color: 'text-rose-400',
          bg: 'bg-rose-500/10 border-rose-500/20',
          barColor: 'bg-rose-500',
          desc: 'Workflow stopped because the maximum number of retry attempts (2) was reached.'
        };
      case 'CUSTOMER_DISPUTED':
        return {
          icon: FileText,
          color: 'text-amber-400',
          bg: 'bg-amber-500/10 border-amber-500/20',
          barColor: 'bg-amber-500',
          desc: 'Automation stopped because customer disputed the charge. Human review is required.'
        };
      case 'CUSTOMER_OPTED_OUT':
        return {
          icon: UserX,
          color: 'text-orange-400',
          bg: 'bg-orange-500/10 border-orange-500/20',
          barColor: 'bg-orange-500',
          desc: 'Automation stopped because the customer opted out of payment recovery.'
        };
      case 'RECOVERY_WINDOW_EXPIRED':
        return {
          icon: Clock,
          color: 'text-slate-400',
          bg: 'bg-slate-500/10 border-slate-500/20',
          barColor: 'bg-slate-500',
          desc: 'Automation stopped because the maximum 7-day recovery window has expired.'
        };
      default:
        return {
          icon: HelpCircle,
          color: 'text-blue-400',
          bg: 'bg-blue-500/10 border-blue-500/20',
          barColor: 'bg-blue-500',
          desc: 'Case flagged for operational intervention or manual review.'
        };
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 shadow-xl space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">Why Automation Stopped</h3>
            <p className="text-xs text-slate-400">Deterministic safe stopping criteria & revenue protection</p>
          </div>
        </div>
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          Guardrail Enforced
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {breakdown.filter(item => item.count > 0).map((item) => {
          const config = getReasonConfig(item.reason);
          const Icon = config.icon;
          return (
            <div
              key={item.reason}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className={`p-1.5 rounded-md border ${config.bg} ${config.color}`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  <div className="text-right">
                    <span className="text-xl font-bold text-white tracking-tight">{item.count}</span>
                    <span className="text-xs text-slate-500 ml-1.5">cases</span>
                  </div>
                </div>
                <h4 className="text-xs font-semibold text-slate-200 mt-3">{item.label}</h4>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{config.desc}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Amount Stopped</span>
                <span className="font-mono font-semibold text-slate-300">
                  ₹{item.amount_at_stop >= 100000 ? `${(item.amount_at_stop / 100000).toFixed(1)}L` : item.amount_at_stop.toLocaleString('en-IN')}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
