import React, { useEffect, useState } from 'react';
import { Users, AlertTriangle, DollarSign, Film } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

import { API_BASE } from '../../config/api';

type JiraIssueRow = {
  id: string;
  key: string;
  summary: string;
  status: string;
  severity: string;
  created: string;
};

type HealthPayload = {
  success?: boolean;
  data?: {
    integrations?: Record<string, boolean>;
    status?: string;
  };
};

const normalizeSeverity = (s: string) => s.trim().toLowerCase();

function buildSparklineFromIssues(
  issues: JiraIssueRow[],
  filter?: (i: JiraIssueRow) => boolean
): { value: number }[] {
  const days = 7;
  const end = new Date();
  end.setHours(0, 0, 0, 0);
  const start = new Date(end);
  start.setDate(start.getDate() - (days - 1));

  const values = Array.from({ length: days }, () => 0);

  for (const issue of issues) {
    if (filter && !filter(issue)) continue;
    const c = new Date(issue.created);
    if (Number.isNaN(c.getTime())) continue;
    c.setHours(0, 0, 0, 0);
    const idx = Math.round((c.getTime() - start.getTime()) / 86400000);
    if (idx >= 0 && idx < days) values[idx] += 1;
  }

  return values.map((value) => ({ value }));
}

function sparklineDiff(sparkline: { value: number }[]): number {
  if (sparkline.length < 2) return 0;
  return sparkline[sparkline.length - 1].value - sparkline[0].value;
}

const healthColors = {
  good: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    icon: 'text-green-400',
    sparkline: '#10b981'
  },
  warning: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    icon: 'text-amber-400',
    sparkline: '#f59e0b'
  },
  critical: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    icon: 'text-red-400',
    sparkline: '#ef4444'
  }
};

type HealthKey = keyof typeof healthColors;

function pickHealthTotalIssues(total: number): HealthKey {
  if (total > 30) return 'critical';
  if (total > 10) return 'warning';
  return 'good';
}

function pickHealthCritical(critical: number): HealthKey {
  if (critical > 5) return 'critical';
  if (critical > 0) return 'warning';
  return 'good';
}

function pickHealthIntegrations(live: number): HealthKey {
  if (live >= 6) return 'good';
  if (live >= 3) return 'warning';
  return 'critical';
}

function pickHealthProduction(critical: number): HealthKey {
  if (critical > 0) return 'critical';
  return 'warning';
}

export function ExecutiveKPIs() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [issues, setIssues] = useState<JiraIssueRow[]>([]);
  const [liveIntegrations, setLiveIntegrations] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [healthRes, issuesRes] = await Promise.all([
          fetch(`${API_BASE}/health`),
          fetch(`${API_BASE}/api/jira/issues`)
        ]);

        if (!healthRes.ok) {
          throw new Error(`Health request failed (${healthRes.status})`);
        }
        if (!issuesRes.ok) {
          throw new Error(`Jira issues request failed (${issuesRes.status})`);
        }

        const healthJson: HealthPayload = await healthRes.json();
        const issuesJson: unknown = await issuesRes.json();

        if (cancelled) return;

        if (healthJson.success === false) {
          throw new Error('Health check reported an error');
        }

        const integrations = healthJson.data?.integrations ?? {};
        const live = Object.values(integrations).filter(Boolean).length;
        setLiveIntegrations(live);

        const list = Array.isArray(issuesJson) ? issuesJson : [];
        setIssues(list as JiraIssueRow[]);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load dashboard data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const totalIssues = issues.length;
  const criticalCount = issues.filter((i) => normalizeSeverity(i.severity) === 'critical').length;

  const sparkTotal = buildSparklineFromIssues(issues);
  const sparkCritical = buildSparklineFromIssues(
    issues,
    (i) => normalizeSeverity(i.severity) === 'critical'
  );
  const sparkIntegrations = Array.from({ length: 7 }, () => ({
    value: Math.max(liveIntegrations, 0)
  }));

  const diffTotal = sparklineDiff(sparkTotal);
  const diffCrit = sparklineDiff(sparkCritical);

  const kpis: {
    label: string;
    value: string;
    change: string;
    health: HealthKey;
    icon: typeof Users;
    sparklineData: { value: number }[];
  }[] = [
    {
      label: 'Total Issues',
      value: String(totalIssues),
      change: `${diffTotal >= 0 ? '+' : ''}${diffTotal} vs week start`,
      health: pickHealthTotalIssues(totalIssues),
      icon: Users,
      sparklineData: sparkTotal
    },
    {
      label: 'Critical Issues',
      value: String(criticalCount),
      change: `${diffCrit >= 0 ? '+' : ''}${diffCrit} vs week start`,
      health: pickHealthCritical(criticalCount),
      icon: AlertTriangle,
      sparklineData: sparkCritical
    },
    {
      label: 'Live Integrations',
      value: String(liveIntegrations),
      change: 'From health check',
      health: pickHealthIntegrations(liveIntegrations),
      icon: DollarSign,
      sparklineData: sparkIntegrations
    },
    {
      label: 'Production Issues',
      value: `${totalIssues} Active`,
      change: `${criticalCount} Critical`,
      health: pickHealthProduction(criticalCount),
      icon: Film,
      sparklineData: sparkTotal
    }
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="border border-slate-800 bg-slate-900/40 rounded-xl p-5 animate-pulse"
          >
            <div className="h-10 w-10 bg-slate-800 rounded-lg mb-4" />
            <div className="h-8 bg-slate-800 rounded w-1/2 mb-2" />
            <div className="h-4 bg-slate-800 rounded w-1/3 mb-4" />
            <div className="h-12 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
        {error}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        const colors = healthColors[kpi.health];

        return (
          <div
            key={index}
            className={`${colors.bg} ${colors.border} border rounded-xl p-5 transition-all hover:scale-105 hover:shadow-lg cursor-pointer relative overflow-hidden`}
          >
            {/* Background Glow */}
            <div className={`absolute inset-0 bg-gradient-to-br ${colors.bg} opacity-50 blur-xl`} />

            <div className="relative">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className={`${colors.bg} p-2.5 rounded-lg`}>
                  <Icon className={`w-5 h-5 ${colors.icon}`} />
                </div>
                <div className="text-right">
                  <div className={`text-xs font-medium ${colors.text}`}>{kpi.change}</div>
                </div>
              </div>

              {/* Value */}
              <div className="mb-3">
                <div className={`text-3xl font-bold ${colors.text} mb-1`}>{kpi.value}</div>
                <div className="text-sm text-slate-400">{kpi.label}</div>
              </div>

              {/* Sparkline */}
              <div className="h-12 -mx-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={kpi.sparklineData}>
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={colors.sparkline}
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Trend Indicator */}
              <div className="mt-2 text-xs text-slate-500">Last 7 days trend</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
