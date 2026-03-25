import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Users, TrendingDown, Loader2 } from 'lucide-react';

import { API_BASE } from '../../config/api';

type Cohort = {
  name: string;
  issues: number;
  risk: 'critical' | 'high' | 'medium';
};

const COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#10b981',
};

function classifyIssue(summary: string): string {
  const s = summary.toLowerCase();
  if (/auth|login|sso|session/.test(s)) return 'Authentication Risk';
  if (/payment|subscription|billing|renewal|pricing/.test(s)) return 'Payment & Revenue Risk';
  if (/cdn|buffer|stream|latency|drm|live.*sport|video|playback/.test(s)) return 'Streaming Infrastructure';
  if (/search|catalog|content|recommendation|discovery/.test(s)) return 'Content Discovery Risk';
  if (/notification|push|alert|analytics|pipeline/.test(s)) return 'Operational Risk';
  if (/geo|region|profile|watch.*history/.test(s)) return 'User Experience Risk';
  return 'Platform Operations';
}

function maxSeverity(issues: { severity: string; summary: string }[]): 'critical' | 'high' | 'medium' {
  let worst: 'critical' | 'high' | 'medium' = 'medium';
  for (const i of issues) {
    if (i.severity === 'critical' || /\bP1\b/.test(i.summary)) return 'critical';
    if (i.severity === 'high' || /\bP2\b/.test(i.summary)) worst = 'high';
  }
  return worst;
}

export function ChurnCohorts() {
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalIssues, setTotalIssues] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jira/issues`);
        if (!res.ok) throw new Error('Failed to fetch issues');
        const issues: { summary: string; severity: string }[] = await res.json();
        setTotalIssues(issues.length);

        const groups: Record<string, { summary: string; severity: string }[]> = {};
        issues.forEach((issue) => {
          const cat = classifyIssue(issue.summary);
          (groups[cat] ??= []).push(issue);
        });

        const mapped: Cohort[] = Object.entries(groups)
          .map(([name, items]) => ({
            name,
            issues: items.length,
            risk: maxSeverity(items),
          }))
          .sort((a, b) => b.issues - a.issues);

        setCohorts(mapped);
      } catch (err: any) {
        console.error('ChurnCohorts fetch error:', err);
        setError(err?.message || 'Failed to load cohorts');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg min-h-[400px]">
        <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <TrendingDown className="w-5 h-5 text-red-400" />
          <span className="text-sm text-red-400">{error}</span>
        </div>
      </div>
    );
  }

  if (cohorts.length === 0) {
    return (
      <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg min-h-[400px] flex flex-col items-center justify-center text-slate-500">
        <Users className="w-10 h-10 mb-3 opacity-40" />
        <p className="text-sm">No issues found to group into cohorts</p>
      </div>
    );
  }

  const criticalCohorts = cohorts.filter((c) => c.risk === 'critical').length;

  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-purple-500/10 p-2 rounded-lg">
            <Users className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Issue Risk Cohorts</h2>
            <p className="text-sm text-slate-400">{totalIssues} issues grouped by service area</p>
          </div>
        </div>
        {criticalCohorts > 0 && (
          <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-lg">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <span className="text-sm font-medium text-red-400">{criticalCohorts} Critical</span>
          </div>
        )}
      </div>

      <div className="h-80 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={cohorts} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} label={{ value: 'Issues', position: 'insideBottom', offset: -5, fill: '#94a3b8', fontSize: 12 }} />
            <YAxis type="category" dataKey="name" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} width={180} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
              formatter={(value: number, _name: string, props: any) => [
                <div key="tt">
                  <div>{value} issue{value !== 1 ? 's' : ''}</div>
                  <div className="text-xs text-slate-400">Risk: {props.payload.risk}</div>
                </div>,
                '',
              ]}
            />
            <Bar dataKey="issues" radius={[0, 8, 8, 0]}>
              {cohorts.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.risk]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {cohorts.slice(0, 2).map((cohort) => (
          <div key={cohort.name} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-[#0064FF] transition-colors">
            <div className="text-xs text-slate-400 mb-2">{cohort.name}</div>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="font-bold text-2xl text-white">{cohort.issues}</span>
              <span className="text-xs text-slate-500">issues</span>
            </div>
            <div className="text-xs text-slate-400">
              Risk: <span className={`font-medium ${COLORS[cohort.risk] === '#ef4444' ? 'text-red-400' : COLORS[cohort.risk] === '#f59e0b' ? 'text-amber-400' : 'text-green-400'}`}>{cohort.risk}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
