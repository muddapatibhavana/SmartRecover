import React from 'react';
import { AlertOctagon, CheckCircle, Sparkles, TrendingUp, ShieldAlert, Users, IndianRupee } from 'lucide-react';
import { DashboardMetrics } from '../types';

interface KPICardsProps {
  metrics: DashboardMetrics | null;
  loading: boolean;
}

export const KPICards: React.FC<KPICardsProps> = ({ metrics, loading }) => {
  const formatCurrency = (val: number) => {
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(1)}L`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const cards = [
    {
      title: 'Failed Mandates',
      value: loading || !metrics ? '...' : metrics.failed_mandates_count.toLocaleString(),
      subtitle: 'Active recurring mandate failures',
      icon: AlertOctagon,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      title: 'Revenue At Risk',
      value: loading || !metrics ? '...' : formatCurrency(metrics.revenue_at_risk),
      subtitle: `Sum of unrecovered mandates`,
      icon: IndianRupee,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      title: 'Recovered Revenue',
      value: loading || !metrics ? '...' : formatCurrency(metrics.recovered_revenue),
      subtitle: `Successfully debited revenue`,
      icon: CheckCircle,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Recovery Rate',
      value: loading || !metrics ? '...' : `${metrics.recovery_rate}%`,
      subtitle: `Target: >60% mandate recovery`,
      icon: TrendingUp,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20'
    },
    {
      title: 'AI Eligible Cases',
      value: loading || !metrics ? '...' : metrics.ai_eligible_count.toLocaleString(),
      subtitle: `Recovery score ≥ 40 / Retry ready`,
      icon: Sparkles,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20'
    },
    {
      title: 'Automation Stopped',
      value: loading || !metrics ? '...' : metrics.automation_stopped_count.toLocaleString(),
      subtitle: `Safely stopped by guardrails`,
      icon: ShieldAlert,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    },
    {
      title: 'Human Review Queue',
      value: loading || !metrics ? '...' : metrics.human_review_count.toLocaleString(),
      subtitle: `Disputes & flagged mandates`,
      icon: Users,
      color: 'text-orange-400',
      bg: 'bg-orange-500/10 border-orange-500/20'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.slice(0, 4).map((c, idx) => {
        const Icon = c.icon;
        return (
          <div
            key={idx}
            className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-all rounded-xl p-5 shadow-lg relative overflow-hidden group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{c.title}</span>
              <div className={`p-2 rounded-lg border ${c.bg} ${c.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold text-white tracking-tight">{c.value}</div>
              <div className="text-xs text-slate-500 mt-1">{c.subtitle}</div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-blue-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        );
      })}

      <div className="col-span-full grid grid-cols-1 sm:grid-cols-3 gap-4">
        {cards.slice(4).map((c, idx) => {
          const Icon = c.icon;
          return (
            <div
              key={idx + 4}
              className="bg-[#111827]/70 border border-[#1F2937] rounded-xl p-4 shadow-sm flex items-center justify-between"
            >
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{c.title}</span>
                <div className="text-xl font-bold text-slate-100 mt-0.5">{c.value}</div>
                <div className="text-[11px] text-slate-500">{c.subtitle}</div>
              </div>
              <div className={`p-2.5 rounded-lg border ${c.bg} ${c.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
