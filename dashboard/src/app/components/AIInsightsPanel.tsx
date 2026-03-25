import { useEffect, useState, useCallback } from 'react';
import { Sparkles, TrendingUp, AlertCircle, Lightbulb, Loader2, Play, CheckCircle } from 'lucide-react';

import { API_BASE } from '../../config/api';

interface AIInsightsPanelProps {
  fullPage?: boolean;
}

type JiraIssue = {
  key: string;
  summary: string;
  severity: string;
  status: string;
  assignee: string;
  url: string;
  team?: string;
};

type Insight = {
  priority: 'critical' | 'high' | 'medium';
  title: string;
  description: string;
  action: string;
  impact: string;
  jiraKey: string;
  url: string;
  service: string;
};

type RcaStatus = {
  has_rca: boolean;
  stage?: string;
};

function extractPriority(summary: string): 'critical' | 'high' | 'medium' {
  if (/\bP1\b/i.test(summary)) return 'critical';
  if (/\bP2\b/i.test(summary)) return 'high';
  return 'medium';
}

function extractService(summary: string): string {
  const lower = summary.toLowerCase();
  if (/auth|login|sso/.test(lower)) return 'Authentication';
  if (/payment|subscription|billing|renewal/.test(lower)) return 'Payments';
  if (/cdn|buffer|stream|latency|drm/.test(lower)) return 'Streaming';
  if (/search|catalog|content|recommendation/.test(lower)) return 'Content';
  if (/analytics|pipeline|event/.test(lower)) return 'Analytics';
  if (/notification|push|alert/.test(lower)) return 'Notifications';
  if (/profile|watch history/.test(lower)) return 'User Profiles';
  if (/geo|region|restriction/.test(lower)) return 'Geo-Compliance';
  return 'Platform';
}

function generateAction(service: string): string {
  const actions: Record<string, string> = {
    Authentication: 'Deploy auth failover cluster',
    Payments: 'Enable payment circuit breaker',
    Streaming: 'Scale CDN edge servers',
    Content: 'Implement catalog cache layer',
    Analytics: 'Fix event pipeline ingestion',
    Notifications: 'Deduplicate notification queue',
    'User Profiles': 'Isolate profile data stores',
    'Geo-Compliance': 'Audit geo-restriction rules',
    Platform: 'Investigate root cause',
  };
  return actions[service] || actions.Platform;
}

function generateImpact(priority: 'critical' | 'high' | 'medium'): string {
  if (priority === 'critical') return 'Immediate resolution required';
  if (priority === 'high') return 'Address within 24 hours';
  return 'Scheduled for next sprint';
}

const priorityConfig = {
  critical: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', badge: 'bg-red-500', label: 'CRITICAL' },
  high: { bg: 'bg-amber-500/20', border: 'border-amber-500/50', text: 'text-amber-400', badge: 'bg-amber-500', label: 'HIGH' },
  medium: { bg: 'bg-blue-500/20', border: 'border-blue-500/50', text: 'text-blue-400', badge: 'bg-blue-500', label: 'MEDIUM' },
};

const iconMap = { critical: AlertCircle, high: TrendingUp, medium: Lightbulb };

export function AIInsightsPanel({ fullPage = false }: AIInsightsPanelProps) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [counts, setCounts] = useState({ critical: 0, high: 0, medium: 0 });
  const [rcaStatuses, setRcaStatuses] = useState<Record<string, RcaStatus>>({});
  const [triggeringRca, setTriggeringRca] = useState<string | null>(null);

  const triggerRca = useCallback(async (insight: Insight) => {
    setTriggeringRca(insight.jiraKey);
    try {
      const res = await fetch(`${API_BASE}/api/rca/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: insight.jiraKey,
          summary: insight.description,
          service: insight.service.toLowerCase(),
          priority: insight.priority,
          description: insight.description,
        }),
      });
      
      if (res.ok) {
        const data = await res.json();
        setRcaStatuses(prev => ({
          ...prev,
          [insight.jiraKey]: { has_rca: true, stage: data.stage }
        }));
      } else {
        const err = await res.json();
        alert(`RCA Failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      alert('Failed to trigger RCA pipeline');
    } finally {
      setTriggeringRca(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jira/issues`);
        if (!res.ok) throw new Error('Failed to fetch issues');
        const issues: JiraIssue[] = await res.json();

        const mapped: Insight[] = issues.map((issue) => {
          const priority = extractPriority(issue.summary);
          const service = extractService(issue.summary);
          const cleanSummary = issue.summary.replace(/^P[123]\s*-\s*/i, '').replace(/^Task\s*-\s*/i, '');
          return {
            priority,
            title: `${service} — ${issue.key}`,
            description: cleanSummary,
            action: generateAction(service),
            impact: generateImpact(priority),
            jiraKey: issue.key,
            url: issue.url,
            service,
          };
        });

        mapped.sort((a, b) => {
          const order = { critical: 0, high: 1, medium: 2 };
          return order[a.priority] - order[b.priority];
        });

        const c = { critical: 0, high: 0, medium: 0 };
        mapped.forEach((i) => c[i.priority]++);
        setCounts(c);
        setInsights(mapped);

        // Fetch RCA statuses
        const keys = mapped.map(i => i.jiraKey).filter(Boolean);
        if (keys.length > 0) {
          const rcaRes = await fetch(`${API_BASE}/api/rca/status/batch?jira_keys=${keys.join(',')}`);
          if (rcaRes.ok) {
            const rcaData = await rcaRes.json();
            setRcaStatuses(rcaData.statuses || {});
          }
        }
      } catch (err: any) {
        console.error('AIInsightsPanel fetch error:', err);
        setError(err?.message || 'Failed to load insights');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-700/50 shadow-2xl">
      <div className="absolute inset-0 bg-gradient-to-br from-[#0064FF]/20 via-purple-600/20 to-[#0064FF]/20 opacity-50" />
      <div className="absolute inset-0 bg-[#0D1117]/80 backdrop-blur-sm" />

      <div className="relative p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#0064FF] to-purple-600 rounded-xl blur-lg opacity-50 animate-pulse" />
              <div className="relative bg-gradient-to-r from-[#0064FF] to-purple-600 p-3 rounded-xl">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">AI-Powered Insights</h2>
              <p className="text-sm text-slate-400">Live analysis from Jira production issues</p>
            </div>
          </div>
          <div className="px-3 py-1 bg-gradient-to-r from-[#0064FF] to-purple-600 rounded-full">
            <span className="text-xs font-bold text-white">Live Data</span>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-[#0064FF] animate-spin" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg mb-4">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <span className="text-sm text-red-400">{error}</span>
          </div>
        ) : insights.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <Sparkles className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm">No production issues found in Jira</p>
          </div>
        ) : (
          <div className={`space-y-4 ${fullPage ? 'max-h-none' : 'max-h-[480px]'} overflow-y-auto pr-1`}>
            {insights.map((insight, index) => {
              const Icon = iconMap[insight.priority];
              const config = priorityConfig[insight.priority];
              const rcaStatus = rcaStatuses[insight.jiraKey];
              const hasRca = rcaStatus?.has_rca;
              const isTriggering = triggeringRca === insight.jiraKey;
              
              return (
                <div
                  key={index}
                  className={`${config.bg} ${config.border} border rounded-xl p-5 transition-all hover:shadow-lg group`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`${config.bg} p-3 rounded-lg flex-shrink-0`}>
                      <Icon className={`w-5 h-5 ${config.text}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <h3 
                            className="font-bold text-white group-hover:text-[#0064FF] transition-colors cursor-pointer truncate"
                            onClick={() => window.open(insight.url, '_blank', 'noopener,noreferrer')}
                          >
                            {insight.title}
                          </h3>
                          <span className={`${config.badge} px-2 py-0.5 rounded text-xs font-bold text-white flex-shrink-0`}>{config.label}</span>
                        </div>
                        {/* RCA Button */}
                        {hasRca ? (
                          <div className="flex items-center gap-1 px-2 py-1 bg-green-500/10 border border-green-500/30 rounded-lg flex-shrink-0">
                            <CheckCircle className="w-3 h-3 text-green-400" />
                            <span className="text-xs font-medium text-green-400 capitalize">{rcaStatus?.stage?.replace('_', ' ') || 'RCA'}</span>
                          </div>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              triggerRca(insight);
                            }}
                            disabled={isTriggering}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#0064FF]/10 border border-[#0064FF]/30 rounded-lg text-xs font-medium text-[#0064FF] hover:bg-[#0064FF]/20 transition-colors disabled:opacity-50 flex-shrink-0"
                          >
                            {isTriggering ? (
                              <>
                                <Loader2 className="w-3 h-3 animate-spin" />
                                Running...
                              </>
                            ) : (
                              <>
                                <Play className="w-3 h-3" />
                                Run RCA
                              </>
                            )}
                          </button>
                        )}
                      </div>
                      <p className="text-sm text-slate-300 mb-3 leading-relaxed">{insight.description}</p>
                      <div className="flex items-center justify-between gap-4 pt-3 border-t border-slate-700/50">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500">Recommended Action:</span>
                          <span className="text-xs font-medium text-[#0064FF]">{insight.action}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3 text-green-400" />
                          <span className="text-xs font-bold text-green-400">{insight.impact}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-slate-700/50">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-red-400">{counts.critical}</div>
              <div className="text-xs text-slate-500">Critical</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-amber-400">{counts.high}</div>
              <div className="text-xs text-slate-500">High Priority</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-400">{counts.medium}</div>
              <div className="text-xs text-slate-500">Medium</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
