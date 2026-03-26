import { useCallback, useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Pagination, usePagination } from "../ui/Pagination";
import { API_BASE } from "../../../config/api";

type GovernanceReview = {
  review_id: string;
  incident_id: string;
  action_type: string;
  risk_tier: string;
  owner: string;
  status: string;
  rationale: string;
  reviewer?: string | null;
  reviewer_comment?: string | null;
  created_at: string;
  updated_at: string;
  expires_at?: string | null;
};

type AuditEntry = {
  review_id: string;
  previous_status: string | null;
  new_status: string;
  actor: string;
  comment: string | null;
  created_at: string;
};

const statusColors: Record<string, string> = {
  awaiting_review: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  approved: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  rejected: "bg-red-500/20 text-red-300 border-red-500/40",
  expired: "bg-slate-500/20 text-slate-400 border-slate-600",
  executed: "bg-blue-500/20 text-blue-300 border-blue-500/40",
  auto_approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  proposed: "bg-slate-500/20 text-slate-300 border-slate-600",
};

const riskColors: Record<string, string> = {
  high: "text-red-400",
  medium: "text-amber-400",
  low: "text-emerald-400",
};

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function slaRemaining(expiresAt: string | null | undefined): string | null {
  if (!expiresAt) return null;
  const diff = new Date(expiresAt).getTime() - Date.now();
  if (diff <= 0) return "OVERDUE";
  const hours = Math.floor(diff / 3_600_000);
  const mins = Math.floor((diff % 3_600_000) / 60_000);
  return `${hours}h ${mins}m remaining`;
}

export function GovernancePanel({
  incidentId,
  embeddedReviews,
}: {
  incidentId?: string | null;
  embeddedReviews?: GovernanceReview[];
}) {
  const [reviews, setReviews] = useState<GovernanceReview[]>(embeddedReviews ?? []);
  const [loading, setLoading] = useState(!embeddedReviews);
  const [auditTrail, setAuditTrail] = useState<Record<string, AuditEntry[]>>({});
  const [expandedReview, setExpandedReview] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const fetchReviews = useCallback(async () => {
    if (embeddedReviews) return;
    setLoading(true);
    try {
      const url = incidentId
        ? `${API_BASE}/api/governance/reviews?incident_id=${incidentId}`
        : `${API_BASE}/api/governance/reviews`;
      const res = await fetch(url);
      if (res.ok) setReviews(await res.json());
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, [incidentId, embeddedReviews]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const fetchAudit = async (reviewId: string) => {
    if (auditTrail[reviewId]) {
      setExpandedReview(expandedReview === reviewId ? null : reviewId);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/governance/audit/${reviewId}`);
      if (res.ok) {
        const entries = await res.json();
        setAuditTrail((prev) => ({ ...prev, [reviewId]: entries }));
      }
    } catch {
      /* silent */
    }
    setExpandedReview(expandedReview === reviewId ? null : reviewId);
  };

  const handleAction = async (reviewId: string, action: "approve" | "reject") => {
    setActionLoading(reviewId);
    try {
      const res = await fetch(`${API_BASE}/api/governance/reviews/${reviewId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer: "dashboard_user", comment: `${action}d via dashboard` }),
      });
      if (res.ok) {
        await fetchReviews();
        if (auditTrail[reviewId]) {
          const auditRes = await fetch(`${API_BASE}/api/governance/audit/${reviewId}`);
          if (auditRes.ok) {
            setAuditTrail((prev) => ({ ...prev, [reviewId]: auditRes.ok ? [] : prev[reviewId] }));
            const entries = await auditRes.json();
            setAuditTrail((prev) => ({ ...prev, [reviewId]: entries }));
          }
        }
      }
    } catch {
      /* silent */
    } finally {
      setActionLoading(null);
    }
  };

  const pendingCount = reviews.filter((r) => r.status === "awaiting_review").length;

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-slate-400" />
          Governance &amp; Approvals
        </h3>
        {pendingCount > 0 && (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-500/20 text-amber-300">
            {pendingCount} pending
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : reviews.length === 0 ? (
        <p className="text-sm text-slate-500">No governance reviews for this incident.</p>
      ) : (
        <>
          <div className="space-y-3">
            {usePagination(reviews, pageSize, page).map((review) => {
            const sla = slaRemaining(review.expires_at);
            const isExpanded = expandedReview === review.review_id;
            const statusStyle = statusColors[review.status] ?? statusColors.proposed;

            return (
              <div
                key={review.review_id || review.action_type}
                className="rounded-lg border border-slate-800 bg-slate-900/50 p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-white">
                        {review.action_type.replace(/_/g, " ")}
                      </span>
                      <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${statusStyle}`}>
                        {review.status.replace(/_/g, " ")}
                      </span>
                      <span className={`text-[10px] uppercase ${riskColors[review.risk_tier] ?? "text-slate-400"}`}>
                        {review.risk_tier} risk
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-2">{review.rationale}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                      <span>Owner: {review.owner}</span>
                      {sla && (
                        <span className={`flex items-center gap-1 ${sla === "OVERDUE" ? "text-red-400" : "text-amber-400"}`}>
                          <Clock className="w-3 h-3" />
                          {sla}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {review.status === "awaiting_review" && (
                      <>
                        <button
                          onClick={() => handleAction(review.review_id, "approve")}
                          disabled={actionLoading === review.review_id}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 text-xs font-medium transition-colors"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Approve
                        </button>
                        <button
                          onClick={() => handleAction(review.review_id, "reject")}
                          disabled={actionLoading === review.review_id}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 text-xs font-medium transition-colors"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          Reject
                        </button>
                      </>
                    )}
                    {review.review_id && (
                      <button
                        onClick={() => fetchAudit(review.review_id)}
                        className="text-xs text-slate-500 hover:text-slate-300 underline"
                      >
                        {isExpanded ? "Hide audit" : "Audit trail"}
                      </button>
                    )}
                  </div>
                </div>

                {isExpanded && auditTrail[review.review_id] && (
                  <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                    {auditTrail[review.review_id].map((entry, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <span className="text-slate-600 font-mono shrink-0">{formatTs(entry.created_at)}</span>
                        <span className="text-slate-400">
                          {entry.actor}: {entry.previous_status ?? "—"} → {entry.new_status}
                          {entry.comment && <span className="text-slate-500 ml-1">({entry.comment})</span>}
                        </span>
                      </div>
                    ))}
                    {auditTrail[review.review_id].length === 0 && (
                      <p className="text-xs text-slate-600">No audit entries yet.</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          </div>
          {reviews.length > 0 && (
            <Pagination
              currentPage={page}
              totalItems={reviews.length}
              pageSize={pageSize}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
            />
          )}
        </>
      )}
    </div>
  );
}
