import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock3,
  Loader2,
  RefreshCw,
  RotateCcw,
  XCircle,
} from "lucide-react";
import { API_BASE } from "../../../config/api";

type PipelineRecord = {
  rca_id: string;
  jira_ticket_id: string;
  service_name?: string | null;
  stage: string;
  created_at: string;
  updated_at?: string | null;
  retry_count: number;
  max_retries?: number;
  failure_reason?: string | null;
};

type PipelineHealth = {
  status: string;
  last_heartbeat: string | null;
  metrics: {
    recent_pipelines: number;
    completed: number;
    failed: number;
    pending_review: number;
    retriable_failures: number;
    success_rate_percent: number;
    avg_cycle_time_hours: number | null;
    avg_review_wait_hours: number | null;
  };
  sla: {
    review_sla_hours: number;
    pending_reviews_count: number;
  };
  timestamp: string;
};

type PipelineMetrics = {
  rca_id: string;
  jira_ticket_id: string;
  stage: string;
  cycle_time: {
    total_hours: number | null;
    time_to_review_hours: number | null;
    review_wait_hours: number | null;
  };
  retry_count: number;
  integrity: {
    hash_present: boolean;
    verified: boolean | null;
  };
};

const STAGE_STYLE: Record<string, { label: string; className: string }> = {
  intake: { label: "Intake", className: "bg-blue-500/10 text-blue-400 border-blue-500/30" },
  evidence_capture: { label: "Evidence", className: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30" },
  summarization: { label: "Summarization", className: "bg-purple-500/10 text-purple-400 border-purple-500/30" },
  testrail_match: { label: "TestRail Match", className: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
  test_generation: { label: "Test Generation", className: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
  review_pending: { label: "Review Pending", className: "bg-yellow-500/10 text-yellow-300 border-yellow-500/30" },
  review_approved: { label: "Review Approved", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" },
  review_rejected: { label: "Review Rejected", className: "bg-rose-500/10 text-rose-400 border-rose-500/30" },
  testrail_write: { label: "TestRail Write", className: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30" },
  verification_pending: {
    label: "Verification Pending",
    className: "bg-sky-500/10 text-sky-400 border-sky-500/30",
  },
  verification_complete: {
    label: "Verification Complete",
    className: "bg-teal-500/10 text-teal-400 border-teal-500/30",
  },
  blast_radius: { label: "Blast Radius", className: "bg-violet-500/10 text-violet-400 border-violet-500/30" },
  jira_close: { label: "Jira Close", className: "bg-lime-500/10 text-lime-400 border-lime-500/30" },
  completed: { label: "Completed", className: "bg-green-500/10 text-green-400 border-green-500/30" },
  failed: { label: "Failed", className: "bg-red-500/10 text-red-400 border-red-500/30" },
};

export function PipelineStatusPage() {
  const [health, setHealth] = useState<PipelineHealth | null>(null);
  const [records, setRecords] = useState<PipelineRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState("all");
  const [resumingRca, setResumingRca] = useState<string | null>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<PipelineMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [healthRes, listRes] = await Promise.all([
        fetch(`${API_BASE}/api/rca/health`),
        fetch(`${API_BASE}/api/rca/pipeline?limit=100`),
      ]);

      if (!healthRes.ok || !listRes.ok) {
        throw new Error("Failed to load pipeline status");
      }

      const healthData = await healthRes.json();
      const listData = await listRes.json();

      setHealth(healthData);
      setRecords(listData.records || []);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch pipeline status");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredRecords = useMemo(() => {
    if (selectedStage === "all") {
      return records;
    }
    return records.filter((r) => r.stage === selectedStage);
  }, [records, selectedStage]);

  const handleResume = async (rcaId: string) => {
    setResumingRca(rcaId);
    try {
      const response = await fetch(`${API_BASE}/api/rca/pipeline/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rca_id: rcaId }),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail || "Resume failed");
      }

      await fetchData(true);
    } catch (err: any) {
      setError(err?.message || "Resume failed");
    } finally {
      setResumingRca(null);
    }
  };

  const handleViewMetrics = async (rcaId: string) => {
    setMetricsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/rca/pipeline/${rcaId}/metrics`);
      if (!response.ok) {
        throw new Error("Failed to load metrics");
      }
      const data = await response.json();
      setSelectedMetrics(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load metrics");
    } finally {
      setMetricsLoading(false);
    }
  };

  const stageOptions = useMemo(() => {
    const unique = Array.from(new Set(records.map((r) => r.stage)));
    return ["all", ...unique];
  }, [records]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/30">
              <Activity className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Pipeline Status</h2>
              <p className="text-sm text-slate-400">
                Live RCA pipeline health, stage progress, and retry controls
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors disabled:opacity-60"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {health && (
        <div className="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-8 gap-4">
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Health</p>
            <p
              className={`mt-1 text-lg font-semibold ${
                health.status === "healthy" ? "text-green-400" : "text-amber-400"
              }`}
            >
              {health.status}
            </p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Success Rate</p>
            <p className="mt-1 text-lg font-semibold text-emerald-400">
              {health.metrics.success_rate_percent}%
            </p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Recent Runs</p>
            <p className="mt-1 text-lg font-semibold text-white">{health.metrics.recent_pipelines}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Completed</p>
            <p className="mt-1 text-lg font-semibold text-green-400">{health.metrics.completed}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Failed</p>
            <p className="mt-1 text-lg font-semibold text-red-400">{health.metrics.failed}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Pending Review</p>
            <p className="mt-1 text-lg font-semibold text-yellow-300">{health.metrics.pending_review}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Avg Cycle (h)</p>
            <p className="mt-1 text-lg font-semibold text-blue-300">
              {health.metrics.avg_cycle_time_hours ?? "—"}
            </p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-xs text-slate-400 uppercase">Retriable</p>
            <p className="mt-1 text-lg font-semibold text-orange-300">
              {health.metrics.retriable_failures}
            </p>
          </div>
        </div>
      )}

      <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between gap-3">
          <h3 className="text-white font-semibold">Recent Pipeline Runs</h3>
          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm"
          >
            {stageOptions.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "All Stages" : s}
              </option>
            ))}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#0D1117]">
              <tr>
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">Jira</th>
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">RCA ID</th>
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">Service</th>
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">Stage</th>
                <th className="px-6 py-3 text-center text-xs text-slate-400 uppercase">Retry</th>
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">Updated</th>
                <th className="px-6 py-3 text-right text-xs text-slate-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredRecords.map((r) => {
                const stage = STAGE_STYLE[r.stage] || {
                  label: r.stage,
                  className: "bg-slate-500/10 text-slate-300 border-slate-500/30",
                };
                const canRetry = r.stage === "failed" && r.retry_count < (r.max_retries ?? 3);
                return (
                  <tr key={r.rca_id} className="hover:bg-slate-800/30">
                    <td className="px-6 py-4 text-sm text-blue-300">{r.jira_ticket_id}</td>
                    <td className="px-6 py-4 text-sm text-slate-300 font-mono">{r.rca_id}</td>
                    <td className="px-6 py-4 text-sm text-slate-400">{r.service_name || "—"}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${stage.className}`}
                      >
                        {stage.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center text-sm text-slate-400">
                      {r.retry_count}/{r.max_retries ?? 3}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {new Date(r.updated_at || r.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleViewMetrics(r.rca_id)}
                          disabled={metricsLoading}
                          className="px-3 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-xs text-slate-100 transition-colors"
                        >
                          Metrics
                        </button>
                        {canRetry && (
                          <button
                            onClick={() => handleResume(r.rca_id)}
                            disabled={resumingRca === r.rca_id}
                            className="px-3 py-1.5 rounded-md bg-orange-500/20 hover:bg-orange-500/30 text-xs text-orange-300 border border-orange-500/30 transition-colors inline-flex items-center gap-1"
                          >
                            {resumingRca === r.rca_id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <RotateCcw className="w-3 h-3" />
                            )}
                            Resume
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {selectedMetrics && (
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-semibold">Pipeline Metrics: {selectedMetrics.rca_id}</h3>
            <span className="text-sm text-slate-400">{selectedMetrics.jira_ticket_id}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-4">
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <p className="text-xs text-slate-500 uppercase">Total Cycle</p>
              <p className="text-lg text-white mt-1">
                {selectedMetrics.cycle_time.total_hours ?? "—"}h
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <p className="text-xs text-slate-500 uppercase">Time to Review</p>
              <p className="text-lg text-blue-300 mt-1">
                {selectedMetrics.cycle_time.time_to_review_hours ?? "—"}h
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <p className="text-xs text-slate-500 uppercase">Review Wait</p>
              <p className="text-lg text-yellow-200 mt-1">
                {selectedMetrics.cycle_time.review_wait_hours ?? "—"}h
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <p className="text-xs text-slate-500 uppercase">Retry Count</p>
              <p className="text-lg text-slate-100 mt-1">{selectedMetrics.retry_count}</p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <p className="text-xs text-slate-500 uppercase">Integrity</p>
              <p className="mt-1 inline-flex items-center gap-1 text-sm">
                {selectedMetrics.integrity.verified ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span className="text-green-400">Verified</span>
                  </>
                ) : selectedMetrics.integrity.hash_present ? (
                  <>
                    <XCircle className="w-4 h-4 text-red-400" />
                    <span className="text-red-400">Mismatch</span>
                  </>
                ) : (
                  <>
                    <Clock3 className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-400">No Hash</span>
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
