import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Gauge,
  ShieldCheck,
  Clock3,
  Activity,
  RefreshCw,
  ArrowRight,
} from "lucide-react";

import { API_BASE } from "../../../config/api";
import { Pagination, usePagination } from "../ui/Pagination";
import { OpsChatbotPanel } from "./OpsChatbotPanel";

type IncidentCard = {
  incident_id: string;
  summary: string;
  service: string;
  severity: string;
  status: string;
  team?: string | null;
  cost_impact: number;
  delay_days: number;
  pipeline_stage?: string | null;
  priority_score: number;
  confidence_score: number;
  top_action?: string | null;
  top_action_confidence?: number | null;
};

type MissionSummary = {
  generated_at: string;
  system_mode: { mode: "mock" | "hybrid" | "live" | string };
  highest_priority_incident: IncidentCard | null;
  open_action_queue: number;
  pending_approvals: number;
  open_incidents: number;
  decision_summary: string;
};

const modeClass: Record<string, string> = {
  live: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  hybrid: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  mock: "bg-slate-500/15 text-slate-300 border-slate-500/40",
};

function formatUsd(value: number): string {
  if (!Number.isFinite(value)) return "$0";
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${Math.round(value).toLocaleString()}`;
}

export function MissionControlPage({ onNavigateToIncident }: { onNavigateToIncident?: (id: string) => void }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<MissionSummary | null>(null);
  const [incidents, setIncidents] = useState<IncidentCard[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const fetchMissionControl = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, incidentsRes] = await Promise.all([
        fetch(`${API_BASE}/api/mission-control/summary`),
        fetch(`${API_BASE}/api/mission-control/incidents?limit=12`),
      ]);
      if (!summaryRes.ok) {
        throw new Error(`Mission summary failed (${summaryRes.status})`);
      }
      if (!incidentsRes.ok) {
        throw new Error(`Incident queue failed (${incidentsRes.status})`);
      }
      setSummary(await summaryRes.json());
      setIncidents(await incidentsRes.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load mission control");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMissionControl();
  }, [fetchMissionControl]);

  const mode = summary?.system_mode.mode ?? "unknown";
  const modeStyle = modeClass[mode] ?? "bg-slate-700/30 text-slate-200 border-slate-600";

  const topIncident = useMemo(() => summary?.highest_priority_incident ?? null, [summary]);

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Mission Control</h2>
          <p className="text-sm text-slate-400">
            Detect, explain, approve, validate, and track incident recovery.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full border text-xs uppercase tracking-wider ${modeStyle}`}>
            Mode: {mode}
          </span>
          <button
            onClick={fetchMissionControl}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm text-slate-200"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
            <Activity className="w-4 h-4" />
            Open Incidents
          </div>
          <div className="mt-2 text-2xl font-bold text-white">{summary?.open_incidents ?? "-"}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
            <Gauge className="w-4 h-4" />
            Action Queue
          </div>
          <div className="mt-2 text-2xl font-bold text-white">{summary?.open_action_queue ?? "-"}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            Pending Approvals
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-300">{summary?.pending_approvals ?? "-"}</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider">
            <Clock3 className="w-4 h-4" />
            Decision Loop
          </div>
          <div className="mt-2 text-sm font-medium text-slate-200">
            {summary?.decision_summary ?? "Waiting for incident data"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 rounded-xl border border-slate-800 bg-[#0D1117] p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-white mb-4">
            <AlertTriangle className="w-4 h-4 text-red-300" />
            Highest Priority Incident
          </div>
          {loading ? (
            <p className="text-sm text-slate-400">Loading incident intelligence...</p>
          ) : topIncident ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">{topIncident.incident_id}</p>
                <h3 className="text-lg font-semibold text-white mt-1">{topIncident.summary}</h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="rounded-lg bg-slate-900/70 border border-slate-800 p-3">
                  <p className="text-slate-500 text-xs">Priority Score</p>
                  <p className="text-white font-semibold">{topIncident.priority_score.toFixed(1)}</p>
                </div>
                <div className="rounded-lg bg-slate-900/70 border border-slate-800 p-3">
                  <p className="text-slate-500 text-xs">Confidence</p>
                  <p className="text-white font-semibold">{topIncident.confidence_score.toFixed(1)}%</p>
                </div>
                <div className="rounded-lg bg-slate-900/70 border border-slate-800 p-3">
                  <p className="text-slate-500 text-xs">Cost Impact</p>
                  <p className="text-white font-semibold">{formatUsd(topIncident.cost_impact)}</p>
                </div>
                <div className="rounded-lg bg-slate-900/70 border border-slate-800 p-3">
                  <p className="text-slate-500 text-xs">Pipeline Stage</p>
                  <p className="text-white font-semibold">{topIncident.pipeline_stage ?? "not started"}</p>
                </div>
              </div>
              <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-3 text-sm">
                <p className="text-blue-200">
                  Recommended action:{" "}
                  <span className="font-semibold">{topIncident.top_action ?? "evaluate manually"}</span>
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400">No active incidents detected.</p>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Operator Focus</h3>
          <ul className="space-y-2 text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 mt-0.5 text-slate-500" />
              Validate top incident evidence and timeline.
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 mt-0.5 text-slate-500" />
              Approve high-risk action if confidence is acceptable.
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 mt-0.5 text-slate-500" />
              Confirm verification run status before Jira closure.
            </li>
          </ul>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Prioritized Incident Queue</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-slate-500 border-b border-slate-800">
              <tr>
                <th className="text-left py-2 pr-3">Incident</th>
                <th className="text-left py-2 pr-3">Severity</th>
                <th className="text-left py-2 pr-3">Priority</th>
                <th className="text-left py-2 pr-3">Top Action</th>
                <th className="text-left py-2 pr-3">Stage</th>
              </tr>
            </thead>
            <tbody>
              {usePagination(incidents, pageSize, page).map((incident) => (
                <tr
                  key={incident.incident_id}
                  className="border-b border-slate-900 cursor-pointer hover:bg-slate-800/40 transition-colors"
                  onClick={() => onNavigateToIncident?.(incident.incident_id)}
                >
                  <td className="py-2 pr-3 text-slate-200">
                    <div className="font-medium text-blue-400 hover:underline">{incident.incident_id}</div>
                    <div className="text-xs text-slate-500 line-clamp-1">{incident.summary}</div>
                  </td>
                  <td className="py-2 pr-3 text-slate-300">{incident.severity}</td>
                  <td className="py-2 pr-3 text-slate-300">{incident.priority_score.toFixed(1)}</td>
                  <td className="py-2 pr-3 text-slate-300">{incident.top_action ?? "-"}</td>
                  <td className="py-2 pr-3 text-slate-300">{incident.pipeline_stage ?? "-"}</td>
                </tr>
              ))}
              {!loading && incidents.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-5 text-center text-slate-500">
                    No incidents available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {incidents.length > 0 && (
            <Pagination
              currentPage={page}
              totalItems={incidents.length}
              pageSize={pageSize}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
            />
          )}
        </div>
      </div>

      <OpsChatbotPanel incidentId={topIncident?.incident_id ?? null} />
    </section>
  );
}
