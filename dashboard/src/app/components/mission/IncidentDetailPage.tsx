import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  AlertTriangle,
  Gauge,
  ShieldCheck,
  GitBranch,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
} from "lucide-react";
import { API_BASE } from "../../../config/api";
import { IncidentTimeline } from "./IncidentTimeline";
import { GovernancePanel } from "./GovernancePanel";
import { BlastRadiusGraph } from "./BlastRadiusGraph";

type ActionRecommendation = {
  action_type: string;
  rank: number;
  risk_tier: string;
  owner: string;
  confidence: number;
  expected_business_impact_usd: number;
  rationale: string;
  explanation: string;
  evidence_refs: string[];
  validation_plan: string[];
  escalation_path?: string | null;
  status: string;
};

type DecisionScoring = {
  operational_severity_score: number;
  subscriber_impact_score: number;
  business_risk_score: number;
  confidence_score: number;
  priority_score: number;
};

type IncidentDetail = {
  incident: {
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
  };
  decision: {
    scoring: DecisionScoring;
    recommended_actions: ActionRecommendation[];
    signals: { signal_key: string; signal_value: string; source: string; weight: number }[];
    summary: string;
  };
  timeline: any;
  governance_reviews: any[];
  rca_id?: string | null;
  verification?: {
    all_passed: boolean;
    total_tests: number;
    passed_tests: number;
    failed_tests: number;
  } | null;
};

function formatUsd(value: number): string {
  if (!Number.isFinite(value)) return "$0";
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${Math.round(value).toLocaleString()}`;
}

const severityColor: Record<string, string> = {
  critical: "bg-red-500/20 text-red-300 border-red-500/40",
  high: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  medium: "bg-blue-500/20 text-blue-300 border-blue-500/40",
  low: "bg-slate-500/20 text-slate-300 border-slate-600",
};

const riskTierColor: Record<string, string> = {
  high: "text-red-400",
  medium: "text-amber-400",
  low: "text-emerald-400",
};

function ScoreBar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  const color =
    pct >= 70 ? "bg-red-500" : pct >= 40 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-white font-medium">{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function IncidentDetailPage({
  incidentId,
  onBack,
}: {
  incidentId: string;
  onBack: () => void;
}) {
  const [data, setData] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/mission-control/incident/${incidentId}`);
      if (!res.ok) throw new Error(`Failed to load incident (${res.status})`);
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <button onClick={onBack} className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4" /> Back to Mission Control
        </button>
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error || "Incident data unavailable."}
        </div>
      </div>
    );
  }

  const { incident, decision, timeline, governance_reviews, verification, rca_id } = data;
  const scoring = decision.scoring;
  const actions = decision.recommended_actions;
  const sevStyle = severityColor[incident.severity] ?? severityColor.medium;

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">{incident.incident_id}</h2>
            <span className={`text-[10px] uppercase px-2 py-0.5 rounded border ${sevStyle}`}>
              {incident.severity}
            </span>
            {incident.pipeline_stage && (
              <span className="text-[10px] uppercase px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                {incident.pipeline_stage}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">{incident.summary}</p>
        </div>
      </div>

      {/* Decision Scoring */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-[#0D1117] p-5">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <Gauge className="w-4 h-4 text-slate-400" />
            Decision Scoring
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="rounded-lg bg-slate-900/70 border border-slate-800 p-3 text-center">
              <p className="text-xs text-slate-500">Priority Score</p>
              <p className="text-3xl font-bold text-white mt-1">{scoring.priority_score.toFixed(1)}</p>
            </div>
            <div className="rounded-lg bg-slate-900/70 border border-slate-800 p-3 text-center">
              <p className="text-xs text-slate-500">Cost Impact</p>
              <p className="text-3xl font-bold text-white mt-1">{formatUsd(incident.cost_impact)}</p>
            </div>
          </div>
          <div className="space-y-3">
            <ScoreBar label="Operational Severity" value={scoring.operational_severity_score} />
            <ScoreBar label="Subscriber Impact" value={scoring.subscriber_impact_score} />
            <ScoreBar label="Business Risk" value={scoring.business_risk_score} />
            <ScoreBar label="Confidence" value={scoring.confidence_score} />
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-slate-400" />
            Incident Info
          </h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Service</span>
              <span className="text-white">{incident.service || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Team</span>
              <span className="text-white">{incident.team || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Status</span>
              <span className="text-white">{incident.status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Delay</span>
              <span className="text-white">{incident.delay_days}d</span>
            </div>
            {rca_id && (
              <div className="flex justify-between">
                <span className="text-slate-500">RCA ID</span>
                <span className="text-cyan-400 text-xs font-mono">{rca_id}</span>
              </div>
            )}
          </div>

          {verification && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <h4 className="text-xs font-semibold text-white mb-2 flex items-center gap-2">
                <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                Verification
              </h4>
              <div className="flex items-center gap-2">
                {verification.all_passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className="text-sm text-slate-300">
                  {verification.passed_tests}/{verification.total_tests} passed
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
          <ShieldCheck className="w-4 h-4 text-slate-400" />
          Recommended Actions ({actions.length})
        </h3>
        {actions.length === 0 ? (
          <p className="text-sm text-slate-500">No actions recommended for this incident.</p>
        ) : (
          <div className="space-y-3">
            {actions.map((action, idx) => (
              <div key={idx} className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-white">
                        #{action.rank} {action.action_type.replace(/_/g, " ")}
                      </span>
                      <span className={`text-[10px] uppercase ${riskTierColor[action.risk_tier] ?? "text-slate-400"}`}>
                        {action.risk_tier} risk
                      </span>
                      <span className="text-[10px] text-slate-500">
                        confidence: {(action.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{action.rationale}</p>
                    <p className="text-xs text-slate-500 mt-1">{action.explanation}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-slate-500">Impact</p>
                    <p className="text-sm font-semibold text-white">
                      {formatUsd(action.expected_business_impact_usd)}
                    </p>
                  </div>
                </div>
                {action.validation_plan.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-800">
                    <p className="text-xs text-slate-500 mb-1">Validation Plan</p>
                    <ul className="space-y-1">
                      {action.validation_plan.map((step, si) => (
                        <li key={si} className="text-xs text-slate-400 flex items-start gap-2">
                          <FileText className="w-3 h-3 mt-0.5 text-slate-600 shrink-0" />
                          {step}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Timeline, Governance, Blast Radius */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <IncidentTimeline timeline={timeline} />
        <GovernancePanel incidentId={incidentId} embeddedReviews={governance_reviews} />
      </div>

      <BlastRadiusGraph
        primaryService={incident.service}
        impactedServices={timeline?.impacted_services}
        serviceMap={[]}
      />

      {/* Decision Signals */}
      {decision.signals.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Decision Signals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {decision.signals.map((signal, idx) => (
              <div key={idx} className="rounded-lg bg-slate-900/50 border border-slate-800 px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">{signal.signal_key}</span>
                  <span className="text-[10px] text-slate-600">{signal.source}</span>
                </div>
                <p className="text-sm text-white font-medium mt-0.5">{signal.signal_value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
