import React from 'react';
import { History, Shield, Sparkles, Cpu, User, CreditCard, ArrowRight } from 'lucide-react';
import { AuditLogEntry } from '../types';

interface AuditTimelineProps {
  logs: AuditLogEntry[];
  loading?: boolean;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ logs, loading = false }) => {
  const getActorConfig = (actor: string) => {
    switch (actor) {
      case 'RECOVERY_INTELLIGENCE':
        return { icon: Sparkles, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30', label: 'AI Intelligence' };
      case 'GUARDRAIL_ENGINE':
        return { icon: Shield, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/30', label: 'Guardrail Engine' };
      case 'PAYMENT_SIMULATOR':
        return { icon: CreditCard, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', label: 'Payment Simulator' };
      case 'HUMAN_OPERATOR':
        return { icon: User, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30', label: 'Human Operator' };
      default:
        return { icon: Cpu, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/30', label: 'Workflow Engine' };
    }
  };

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts;
    }
  };

  const formatDate = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        Loading immutable audit trail...
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400 text-xs">
        No audit events recorded for this case yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center space-x-2 text-slate-300">
          <History className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-bold uppercase tracking-wider">Immutable Audit Trail</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">
          {logs.length} events logged
        </span>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-800">
        {logs.map((log) => {
          const actorConf = getActorConfig(log.actor);
          const ActorIcon = actorConf.icon;

          return (
            <div key={log.id} className="relative group">
              {/* Dot Icon */}
              <div className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full border flex items-center justify-center ${actorConf.bg} ${actorConf.color}`}>
                <ActorIcon className="w-3 h-3" />
              </div>

              {/* Card */}
              <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-3.5 hover:border-slate-700 transition-all space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${actorConf.bg} ${actorConf.color}`}>
                      {actorConf.label}
                    </span>
                    <span className="text-xs font-semibold text-white">{log.event_type}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    <span>{formatDate(log.timestamp)}</span> <span className="text-slate-200">{formatTime(log.timestamp)}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{log.description}</p>

                {/* State Transition Badges */}
                {(log.state_before || log.state_after) && (
                  <div className="pt-2 flex items-center space-x-2 text-[10px] font-mono">
                    <span className="text-slate-500">Transition:</span>
                    <span className="px-1.5 py-0.5 bg-slate-800 text-slate-300 rounded border border-slate-700">
                      {log.state_before || 'INITIAL'}
                    </span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                    <span className="px-1.5 py-0.5 bg-blue-950 text-blue-300 rounded border border-blue-800">
                      {log.state_after || 'CURRENT'}
                    </span>
                  </div>
                )}

                {/* Metadata JSON preview if present */}
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <div className="pt-1 text-[10px] font-mono text-slate-500 bg-slate-950/40 p-2 rounded border border-slate-800/60 overflow-x-auto">
                    {JSON.stringify(log.metadata)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
