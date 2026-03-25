import React, { useEffect, useState } from 'react';
import { Film, ExternalLink, Clock, DollarSign } from 'lucide-react';

import { API_BASE } from '../../config/api';

type JiraIssueApi = {
  id: string;
  key: string;
  summary: string;
  status: string;
  severity: string;
  show_name?: string;
  cost_impact?: number;
  delay_days?: number;
  created: string;
  updated: string;
  assignee?: string;
  url: string;
};

type SeverityKey = 'critical' | 'high' | 'medium';

const severityConfig: Record<
  SeverityKey,
  { dot: string; bg: string; text: string; border: string }
> = {
  critical: {
    dot: '🔴',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/30'
  },
  high: {
    dot: '🟡',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30'
  },
  medium: {
    dot: '🟢',
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    border: 'border-green-500/30'
  }
};

function mapSeverity(raw: string): SeverityKey {
  const s = raw.trim().toLowerCase();
  if (s === 'critical') return 'critical';
  if (s === 'high') return 'high';
  return 'medium';
}

function extractPriority(summary: string): string | null {
  const m = summary.match(/^(P[123])\s*[-–]\s*/i);
  return m ? m[1].toUpperCase() : null;
}

function stripPriorityPrefix(summary: string): string {
  return summary.replace(/^(P[123])\s*[-–]\s*/i, '').trim() || summary;
}

function formatCostUsd(n: number | undefined): string {
  if (n == null || Number.isNaN(n)) return '$0';
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function isResolvedStatus(status: string): boolean {
  return /^(done|resolved|closed|complete)/i.test(status.trim());
}

export function ProductionIssuesTable() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [issues, setIssues] = useState<JiraIssueApi[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/api/jira/issues`);
        if (!res.ok) {
          throw new Error(`Request failed (${res.status})`);
        }
        const data: unknown = await res.json();
        if (cancelled) return;
        setIssues(Array.isArray(data) ? (data as JiraIssueApi[]) : []);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load issues');
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

  const handleOpenIssue = (url: string) => {
    if (!url) return;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const criticalCount = issues.filter((i) => mapSeverity(i.severity) === 'critical').length;
  const highCount = issues.filter((i) => mapSeverity(i.severity) === 'high').length;

  const totalCost = issues.reduce((acc, i) => acc + (i.cost_impact ?? 0), 0);
  const totalDelays = issues.reduce((acc, i) => acc + (i.delay_days ?? 0), 0);
  const uniqueShows = new Set(
    issues.map((i) => (i.show_name && i.show_name.trim() ? i.show_name.trim() : i.key))
  ).size;
  const resolved = issues.filter((i) => isResolvedStatus(i.status)).length;
  const resolutionRate = issues.length ? Math.round((resolved / issues.length) * 100) : 0;

  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-[#0064FF]/10 p-2 rounded-lg">
            <Film className="w-5 h-5 text-[#0064FF]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Production Issues Tracker</h2>
            <p className="text-sm text-slate-400">Active delays and cost impacts</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-xs text-red-400 font-medium min-w-[7rem] text-center">
            {loading ? '…' : `${criticalCount} Critical`}
          </div>
          <div className="px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full text-xs text-amber-400 font-medium min-w-[8rem] text-center">
            {loading ? '…' : `${highCount} High Priority`}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Severity
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Show Name
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Status
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Cost Impact
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Days Delayed
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Department
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              [0, 1, 2, 3, 4].map((i) => (
                <tr key={`sk-${i}`} className="border-b border-slate-800/50">
                  <td colSpan={7} className="py-4 px-4">
                    <div className="h-10 w-full animate-pulse rounded bg-slate-800/80" />
                  </td>
                </tr>
              ))}

            {!loading &&
              issues.map((issue) => {
                const sev = mapSeverity(issue.severity);
                const config = severityConfig[sev];
                const showLabel =
                  issue.show_name && issue.show_name.trim()
                    ? issue.show_name.trim()
                    : issue.key || issue.id;
                const priority = extractPriority(issue.summary);
                const narrative = stripPriorityPrefix(issue.summary);
                const dept = issue.assignee?.trim() || '—';

                return (
                  <tr
                    key={issue.key || issue.id}
                    onClick={() => handleOpenIssue(issue.url)}
                    className={`border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors group`}
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{config.dot}</span>
                        <span className={`text-xs font-medium ${config.text} capitalize`}>
                          {sev}
                          {priority ? (
                            <span className="text-slate-500 normal-case"> ({priority})</span>
                          ) : null}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <Film className="w-4 h-4 text-slate-500" />
                        <span className="font-medium text-white">{showLabel}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                          {issue.status}
                        </span>
                        <span className="text-sm text-slate-400">{narrative}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <DollarSign className="w-4 h-4 text-red-400" />
                        <span className="font-bold text-red-400">
                          {formatCostUsd(issue.cost_impact)}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Clock className="w-4 h-4 text-amber-400" />
                        <span className="font-bold text-amber-400">
                          {issue.delay_days ?? 0}d
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-sm text-slate-400">{dept}</span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 px-3 py-1 bg-[#0064FF]/10 border border-[#0064FF]/30 rounded-lg text-xs font-medium text-[#0064FF] hover:bg-[#0064FF]/20 transition-colors"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenIssue(issue.url);
                        }}
                      >
                        {issue.key}
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}

            {!loading && issues.length === 0 && !error && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-sm text-slate-500">
                  No production issues returned from Jira.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="mt-6 pt-6 border-t border-slate-800">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-red-400">{formatCostUsd(totalCost)}</div>
            <div className="text-xs text-slate-500">Total Cost Impact</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-400">{totalDelays} Days</div>
            <div className="text-xs text-slate-500">Total Delays</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-[#0064FF]">{uniqueShows} Shows</div>
            <div className="text-xs text-slate-500">Affected Productions</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{resolutionRate}%</div>
            <div className="text-xs text-slate-500">Resolution Rate</div>
          </div>
        </div>
      </div>
    </div>
  );
}
