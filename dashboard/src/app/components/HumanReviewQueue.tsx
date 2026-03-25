import { useEffect, useState, useCallback } from 'react';
import { Clock, CheckCircle, XCircle, AlertTriangle, Users, ExternalLink, Loader2 } from 'lucide-react';
import { API_BASE } from '../../config/api';

type ReviewItem = {
  review_id: string;
  rca_id: string;
  jira_ticket_id: string;
  created_at: string;
  sla_deadline: string;
  status: string;
  cases_count: number;
  is_overdue: boolean;
};

function formatTimeRemaining(deadline: string): { text: string; isUrgent: boolean; isOverdue: boolean } {
  const now = new Date();
  const deadlineDate = new Date(deadline);
  const diff = deadlineDate.getTime() - now.getTime();
  
  if (diff < 0) {
    const hours = Math.abs(Math.floor(diff / (1000 * 60 * 60)));
    return { text: `${hours}h overdue`, isUrgent: true, isOverdue: true };
  }
  
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours < 4) {
    return { text: `${hours}h ${minutes}m left`, isUrgent: true, isOverdue: false };
  }
  
  return { text: `${hours}h ${minutes}m left`, isUrgent: false, isOverdue: false };
}

interface HumanReviewQueueProps {
  fullPage?: boolean;
}

export function HumanReviewQueue({ fullPage = false }: HumanReviewQueueProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [approving, setApproving] = useState<string | null>(null);

  const fetchReviews = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/rca/review/pending`);
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();
      setReviews(data.pending || []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load reviews');
    } finally {
      setLoading(false);
    }
  }, []);

  const approveReview = useCallback(async (item: ReviewItem) => {
    setApproving(item.review_id);
    try {
      const res = await fetch(`${API_BASE}/api/rca/review/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rca_id: item.rca_id,
          reviewer_id: 'dashboard_user',
          notes: 'Approved via dashboard',
        }),
      });
      
      if (res.ok) {
        setReviews(prev => prev.filter(r => r.review_id !== item.review_id));
      } else {
        const err = await res.json();
        alert(`Approval failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      alert('Failed to approve review');
    } finally {
      setApproving(null);
    }
  }, []);

  useEffect(() => {
    fetchReviews();
    const interval = setInterval(fetchReviews, 30000);
    return () => clearInterval(interval);
  }, [fetchReviews]);

  const overdueCount = reviews.filter(r => r.is_overdue).length;
  const urgentCount = reviews.filter(r => {
    const { isUrgent } = formatTimeRemaining(r.sla_deadline);
    return isUrgent && !r.is_overdue;
  }).length;

  if (loading) {
    return (
      <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-amber-500/10 p-2 rounded-lg">
            <Users className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Human Review Queue</h3>
            <p className="text-xs text-slate-400">24h SLA for test case approval</p>
          </div>
        </div>
        <div className="animate-pulse space-y-3">
          {[0, 1, 2].map(i => (
            <div key={i} className="h-16 bg-slate-800/60 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#0D1117] border border-red-500/30 rounded-xl p-6">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-amber-500/10 p-2 rounded-lg">
            <Users className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Human Review Queue</h3>
            <p className="text-xs text-slate-400">24h SLA for test case approval</p>
          </div>
        </div>
        <div className="flex gap-2">
          {overdueCount > 0 && (
            <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full flex items-center gap-1.5">
              <AlertTriangle className="w-3 h-3 text-red-400" />
              <span className="text-xs font-medium text-red-400">{overdueCount} Overdue</span>
            </div>
          )}
          {urgentCount > 0 && (
            <div className="px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-amber-400" />
              <span className="text-xs font-medium text-amber-400">{urgentCount} Urgent</span>
            </div>
          )}
        </div>
      </div>

      {/* Queue Items */}
      {reviews.length === 0 ? (
        <div className="text-center py-8">
          <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No pending reviews</p>
          <p className="text-xs text-slate-500">All test cases have been approved</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reviews.map((item) => {
            const timeInfo = formatTimeRemaining(item.sla_deadline);
            const isProcessing = approving === item.review_id;
            
            return (
              <div
                key={item.review_id}
                className={`p-4 rounded-lg border ${
                  timeInfo.isOverdue
                    ? 'bg-red-500/5 border-red-500/30'
                    : timeInfo.isUrgent
                    ? 'bg-amber-500/5 border-amber-500/30'
                    : 'bg-slate-800/30 border-slate-700/50'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-white">{item.jira_ticket_id}</span>
                      <span className="text-xs px-2 py-0.5 bg-slate-700 rounded text-slate-300">
                        {item.cases_count} test case{item.cases_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Clock className={`w-3 h-3 ${timeInfo.isOverdue ? 'text-red-400' : timeInfo.isUrgent ? 'text-amber-400' : 'text-slate-500'}`} />
                      <span className={timeInfo.isOverdue ? 'text-red-400 font-medium' : timeInfo.isUrgent ? 'text-amber-400' : 'text-slate-500'}>
                        {timeInfo.text}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => approveReview(item)}
                      disabled={isProcessing}
                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg text-xs font-medium text-green-400 hover:bg-green-500/20 transition-colors disabled:opacity-50"
                    >
                      {isProcessing ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <CheckCircle className="w-3 h-3" />
                      )}
                      Approve
                    </button>
                    <a
                      href={`${API_BASE}/api/rca/artifact/${item.rca_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-700/50 border border-slate-600/50 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* SLA Notice */}
      {reviews.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <p className="text-xs text-slate-500 text-center">
            AI-generated test cases require human approval before being written to TestRail
          </p>
        </div>
      )}
    </div>
  );
}
