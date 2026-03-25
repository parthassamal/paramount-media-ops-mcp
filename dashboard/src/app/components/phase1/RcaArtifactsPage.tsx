import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  RefreshCw,
  ShieldCheck,
  ShieldX,
  XCircle,
} from "lucide-react";
import { API_BASE } from "../../../config/api";

type PipelineRecord = {
  rca_id: string;
  jira_ticket_id: string;
  service_name?: string | null;
  stage: string;
  jira_closed?: boolean;
  fix_verified?: boolean;
  artifact_hash?: string | null;
  created_at: string;
};

type ArtifactDetails = {
  rca_id: string;
  jira_ticket_id: string;
  stage: string;
  jira_closed: boolean;
  root_cause_summary: string | null;
  evidence: {
    bundle_id: string | null;
    sources: string[];
    error_rate: number | null;
    p99_latency_ms: number | null;
    stack_trace_available: boolean;
  };
  testrail_match: {
    confidence: string | null;
    score: number | null;
    matched_case_id: string | null;
    automation_covered: boolean | null;
    automation_gap_reason: string | null;
  };
  testrail_write: {
    created_case_ids: number[];
    verification_run_id: number | null;
    regression_run_id: number | null;
  };
  blast_radius: {
    impacted_components: string[];
    smoke_scope: number[];
    regression_scope: number[];
  };
  verification: {
    fix_verified: boolean;
    verification_result: {
      all_passed?: boolean;
      failed?: number;
      pass_rate?: number;
      run_id?: number;
    } | null;
    verification_attempts: number;
  };
  remediation_owners: Array<{
    action: string;
    owner: string;
    due_date: string;
    completed: boolean;
  }>;
};

type VerifyResult = {
  verified: boolean | null;
  message: string;
  stored_hash?: string;
  computed_hash?: string;
};

type CanCloseResult = {
  can_close: boolean;
  reason: string;
  validation: {
    is_valid: boolean;
    missing_fields: string[];
  };
};

const STAGE_BADGE: Record<string, string> = {
  completed: "bg-green-500/10 text-green-400 border-green-500/30",
  failed: "bg-red-500/10 text-red-400 border-red-500/30",
  review_pending: "bg-yellow-500/10 text-yellow-300 border-yellow-500/30",
  jira_close: "bg-lime-500/10 text-lime-300 border-lime-500/30",
};

export function RcaArtifactsPage() {
  const [records, setRecords] = useState<PipelineRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRcaId, setSelectedRcaId] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<ArtifactDetails | null>(null);
  const [verify, setVerify] = useState<VerifyResult | null>(null);
  const [canClose, setCanClose] = useState<CanCloseResult | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [stageFilter, setStageFilter] = useState("all");

  const fetchRecords = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const response = await fetch(`${API_BASE}/api/rca/pipeline?limit=100`);
      if (!response.ok) {
        throw new Error("Failed to load RCA records");
      }
      const data = await response.json();
      setRecords(data.records || []);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load RCA records");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const filteredRecords = useMemo(() => {
    if (stageFilter === "all") {
      return records;
    }
    return records.filter((r) => r.stage === stageFilter);
  }, [records, stageFilter]);

  const stageOptions = useMemo(() => {
    const unique = Array.from(new Set(records.map((r) => r.stage)));
    return ["all", ...unique];
  }, [records]);

  const loadArtifact = async (rcaId: string) => {
    setSelectedRcaId(rcaId);
    setDetailsLoading(true);
    try {
      const [artifactRes, verifyRes, canCloseRes] = await Promise.all([
        fetch(`${API_BASE}/api/rca/artifact/${rcaId}`),
        fetch(`${API_BASE}/api/rca/pipeline/${rcaId}/verify`),
        fetch(`${API_BASE}/api/rca/pipeline/${rcaId}/can-close`),
      ]);

      if (!artifactRes.ok) {
        throw new Error("Failed to load artifact");
      }

      const artifactData = await artifactRes.json();
      setArtifact(artifactData);

      if (verifyRes.ok) {
        setVerify(await verifyRes.json());
      } else {
        setVerify(null);
      }

      if (canCloseRes.ok) {
        setCanClose(await canCloseRes.json());
      } else {
        setCanClose(null);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load artifact details");
    } finally {
      setDetailsLoading(false);
    }
  };

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
              <FileText className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">RCA Artifacts</h2>
              <p className="text-sm text-slate-400">
                Browse artifacts, integrity checks, and Jira close readiness
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchRecords(true)}
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

      <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between gap-3">
          <h3 className="text-white font-semibold">Pipeline Records</h3>
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
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
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">Stage</th>
                <th className="px-6 py-3 text-center text-xs text-slate-400 uppercase">Closed</th>
                <th className="px-6 py-3 text-center text-xs text-slate-400 uppercase">Fix Verified</th>
                <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase">Created</th>
                <th className="px-6 py-3 text-right text-xs text-slate-400 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredRecords.map((r) => {
                const badge =
                  STAGE_BADGE[r.stage] || "bg-slate-500/10 text-slate-300 border-slate-500/30";
                return (
                  <tr key={r.rca_id} className="hover:bg-slate-800/30">
                    <td className="px-6 py-4 text-sm text-blue-300">{r.jira_ticket_id}</td>
                    <td className="px-6 py-4 text-sm text-slate-300 font-mono">{r.rca_id}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${badge}`}
                      >
                        {r.stage}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {r.jira_closed ? (
                        <CheckCircle2 className="w-4 h-4 text-green-400 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-slate-500 mx-auto" />
                      )}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {r.fix_verified ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-slate-500 mx-auto" />
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => loadArtifact(r.rca_id)}
                        disabled={detailsLoading && selectedRcaId === r.rca_id}
                        className="px-3 py-1.5 rounded-md bg-blue-500/20 hover:bg-blue-500/30 text-xs text-blue-300 border border-blue-500/30 transition-colors inline-flex items-center gap-1"
                      >
                        {detailsLoading && selectedRcaId === r.rca_id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : null}
                        Open
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {artifact && (
        <div className="space-y-4">
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-white font-semibold">Artifact: {artifact.rca_id}</h3>
                <p className="text-sm text-slate-400">{artifact.jira_ticket_id}</p>
              </div>
              <div className="flex items-center gap-2">
                {verify?.verified ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border bg-green-500/10 text-green-400 border-green-500/30 text-xs">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Integrity Verified
                  </span>
                ) : verify?.verified === false ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border bg-red-500/10 text-red-400 border-red-500/30 text-xs">
                    <ShieldX className="w-3.5 h-3.5" />
                    Integrity Failed
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border bg-slate-500/10 text-slate-400 border-slate-500/30 text-xs">
                    Integrity Pending
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
                <p className="text-xs text-slate-500 uppercase">Stage</p>
                <p className="text-sm text-slate-200 mt-1">{artifact.stage}</p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
                <p className="text-xs text-slate-500 uppercase">Jira Closed</p>
                <p className="text-sm mt-1 text-slate-200">{artifact.jira_closed ? "Yes" : "No"}</p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
                <p className="text-xs text-slate-500 uppercase">Fix Verified</p>
                <p
                  className={`text-sm mt-1 ${
                    artifact.verification.fix_verified ? "text-emerald-400" : "text-slate-300"
                  }`}
                >
                  {artifact.verification.fix_verified ? "Yes" : "No"}
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
                <p className="text-xs text-slate-500 uppercase">Can Close Jira</p>
                <p className={`text-sm mt-1 ${canClose?.can_close ? "text-green-400" : "text-amber-300"}`}>
                  {canClose?.can_close ? "Ready" : "Blocked"}
                </p>
              </div>
            </div>

            {!canClose?.can_close && canClose?.reason && (
              <div className="mt-4 p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-200 text-sm">
                {canClose.reason}
              </div>
            )}
          </div>

          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
            <h4 className="text-white font-semibold mb-2">Root Cause Summary</h4>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
              {artifact.root_cause_summary || "No summary available"}
            </p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
              <h4 className="text-white font-semibold mb-3">Evidence</h4>
              <div className="space-y-2 text-sm">
                <p className="text-slate-400">
                  Sources:{" "}
                  <span className="text-slate-200">
                    {artifact.evidence.sources.length > 0 ? artifact.evidence.sources.join(", ") : "—"}
                  </span>
                </p>
                <p className="text-slate-400">
                  Error Rate: <span className="text-slate-200">{artifact.evidence.error_rate ?? "—"}</span>
                </p>
                <p className="text-slate-400">
                  P99 Latency:{" "}
                  <span className="text-slate-200">
                    {artifact.evidence.p99_latency_ms != null
                      ? `${artifact.evidence.p99_latency_ms} ms`
                      : "—"}
                  </span>
                </p>
                <p className="text-slate-400">
                  Stack Trace:{" "}
                  <span className="text-slate-200">
                    {artifact.evidence.stack_trace_available ? "Available" : "Not captured"}
                  </span>
                </p>
              </div>
            </div>

            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
              <h4 className="text-white font-semibold mb-3">TestRail</h4>
              <div className="space-y-2 text-sm">
                <p className="text-slate-400">
                  Match Confidence:{" "}
                  <span className="text-slate-200">{artifact.testrail_match.confidence || "—"}</span>
                </p>
                <p className="text-slate-400">
                  Match Score: <span className="text-slate-200">{artifact.testrail_match.score ?? "—"}</span>
                </p>
                <p className="text-slate-400">
                  Created Cases:{" "}
                  <span className="text-slate-200">
                    {artifact.testrail_write.created_case_ids.length > 0
                      ? artifact.testrail_write.created_case_ids.join(", ")
                      : "—"}
                  </span>
                </p>
                <p className="text-slate-400">
                  Verification Run:{" "}
                  <span className="text-slate-200">{artifact.testrail_write.verification_run_id ?? "—"}</span>
                </p>
              </div>
            </div>
          </div>

          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
            <h4 className="text-white font-semibold mb-3">Blast Radius</h4>
            <p className="text-sm text-slate-400 mb-2">Impacted Components</p>
            <div className="flex flex-wrap gap-2">
              {artifact.blast_radius.impacted_components.length > 0 ? (
                artifact.blast_radius.impacted_components.map((component) => (
                  <span
                    key={component}
                    className="px-2.5 py-1 rounded-full border bg-violet-500/10 text-violet-300 border-violet-500/30 text-xs"
                  >
                    {component}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500">No impacted components recorded</span>
              )}
            </div>
          </div>

          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
            <h4 className="text-white font-semibold mb-3">Remediation Owners</h4>
            {artifact.remediation_owners.length === 0 ? (
              <p className="text-sm text-slate-500">No remediation actions added yet.</p>
            ) : (
              <div className="space-y-2">
                {artifact.remediation_owners.map((owner, idx) => (
                  <div
                    key={`${owner.owner}-${idx}`}
                    className="p-3 rounded-lg border border-slate-800 bg-slate-900/40"
                  >
                    <p className="text-sm text-slate-200">{owner.action}</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {owner.owner} • due {new Date(owner.due_date).toLocaleDateString()} •{" "}
                      {owner.completed ? "completed" : "open"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {verify?.message && (
            <div
              className={`rounded-xl border p-4 text-sm ${
                verify.verified
                  ? "bg-green-500/10 border-green-500/30 text-green-300"
                  : verify.verified === false
                  ? "bg-red-500/10 border-red-500/30 text-red-300"
                  : "bg-slate-500/10 border-slate-500/30 text-slate-300"
              }`}
            >
              {verify.message}
            </div>
          )}

          {!canClose?.validation.is_valid && canClose?.validation.missing_fields?.length ? (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <h4 className="text-red-300 font-medium mb-2">Missing Required Fields</h4>
              <div className="flex flex-wrap gap-2">
                {canClose.validation.missing_fields.map((field) => (
                  <span
                    key={field}
                    className="px-2 py-1 rounded bg-red-500/20 border border-red-500/30 text-xs text-red-200"
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
