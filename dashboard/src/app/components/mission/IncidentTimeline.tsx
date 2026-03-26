import { Clock, GitBranch, AlertTriangle, Radio, Database } from "lucide-react";

type TimelineEvent = {
  timestamp: string;
  source: string;
  event_type: string;
  summary: string;
  details?: string | null;
  severity?: string | null;
  references?: { ref_type: string; ref_id: string; url?: string }[];
};

type TimelineData = {
  incident_id: string;
  service: string;
  events: TimelineEvent[];
  recommended_severity?: string | null;
  evidence_completeness_score?: number;
};

const sourceConfig: Record<string, { icon: typeof Clock; color: string; bg: string }> = {
  jira: { icon: AlertTriangle, color: "text-blue-400", bg: "bg-blue-500/20" },
  newrelic: { icon: Radio, color: "text-emerald-400", bg: "bg-emerald-500/20" },
  datadog: { icon: Database, color: "text-purple-400", bg: "bg-purple-500/20" },
  pipeline: { icon: GitBranch, color: "text-cyan-400", bg: "bg-cyan-500/20" },
};

function formatTs(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

export function IncidentTimeline({ timeline }: { timeline: TimelineData | null }) {
  if (!timeline || !timeline.events?.length) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" />
          Incident Timeline
        </h3>
        <p className="text-sm text-slate-500">No timeline events available.</p>
      </div>
    );
  }

  const events = [...timeline.events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" />
          Incident Timeline
        </h3>
        {timeline.evidence_completeness_score != null && (
          <span className="text-xs text-slate-400">
            Evidence completeness:{" "}
            <span className="text-white font-medium">
              {Math.round(timeline.evidence_completeness_score * 100)}%
            </span>
          </span>
        )}
      </div>

      <div className="relative pl-6 space-y-0">
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-slate-700" />

        {events.map((event, idx) => {
          const cfg = sourceConfig[event.source] ?? {
            icon: Clock,
            color: "text-slate-400",
            bg: "bg-slate-700/40",
          };
          const Icon = cfg.icon;
          const sevColor =
            event.severity === "critical"
              ? "text-red-400"
              : event.severity === "high"
              ? "text-amber-400"
              : "text-slate-400";

          return (
            <div key={idx} className="relative flex items-start gap-3 pb-4">
              <div
                className={`absolute -left-6 mt-1 w-[22px] h-[22px] rounded-full flex items-center justify-center ${cfg.bg}`}
              >
                <Icon className={`w-3 h-3 ${cfg.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-slate-500 font-mono">{formatTs(event.timestamp)}</span>
                  <span
                    className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded ${cfg.bg} ${cfg.color}`}
                  >
                    {event.source}
                  </span>
                  {event.severity && (
                    <span className={`text-[10px] uppercase tracking-wider ${sevColor}`}>
                      {event.severity}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-200 mt-0.5">{event.summary}</p>
                {event.details && (
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{event.details}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
