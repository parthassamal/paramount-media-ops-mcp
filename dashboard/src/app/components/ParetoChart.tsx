import React, { useEffect, useState } from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";

import { API_BASE } from "../../config/api";

type ParetoRow = {
  category: string;
  count: number;
  cumulative: number;
};

export function ParetoChart() {
  const [data, setData] = useState<ParetoRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [topImpact, setTopImpact] = useState({ pct: 0, count: 0, total: 0 });

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jira/issues`);
        if (!res.ok) throw new Error("Failed to load issues");
        const issues: { summary: string; severity: string }[] = await res.json();

        const buckets: Record<string, number> = { Critical: 0, High: 0, Medium: 0 };
        issues.forEach((i) => {
          const sev = i.severity?.toLowerCase();
          if (sev === "critical" || /\bP1\b/.test(i.summary)) buckets.Critical++;
          else if (sev === "high" || /\bP2\b/.test(i.summary)) buckets.High++;
          else buckets.Medium++;
        });

        const sorted = Object.entries(buckets)
          .filter(([, v]) => v > 0)
          .sort(([, a], [, b]) => b - a);

        const total = sorted.reduce((s, [, v]) => s + v, 0);
        let running = 0;
        const rows: ParetoRow[] = sorted.map(([cat, count]) => {
          running += count;
          return { category: `${cat} (${count})`, count, cumulative: Math.round((running / total) * 100) };
        });

        if (sorted.length > 0) {
          const topCount = sorted[0][1];
          setTopImpact({ pct: Math.round((topCount / total) * 100), count: topCount, total });
        }
        setData(rows);
      } catch (err: any) {
        console.error("ParetoChart fetch error:", err);
        setError(err?.message || "Failed to load chart data");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-[#FF6B00]/10 p-2 rounded-lg">
            <TrendingUp className="w-5 h-5 text-[#FF6B00]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Pareto Analysis</h2>
            <p className="text-sm text-slate-400">Issue distribution by severity</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-[#FF6B00] animate-spin" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <TrendingUp className="w-5 h-5 text-red-400" />
          <span className="text-sm text-red-400">{error}</span>
        </div>
      ) : data.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
          <TrendingUp className="w-10 h-10 mb-3 opacity-40" />
          <p className="text-sm">No issues to analyze</p>
        </div>
      ) : (
        <>
          <div className="h-64 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="category" stroke="#94a3b8" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis yAxisId="left" stroke="#94a3b8" tick={{ fill: "#94a3b8" }} label={{ value: "Issues", angle: -90, position: "insideLeft", fill: "#94a3b8" }} />
                <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" tick={{ fill: "#94a3b8" }} label={{ value: "Cumulative %", angle: 90, position: "insideRight", fill: "#94a3b8" }} />
                <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#f1f5f9" }} />
                <Legend wrapperStyle={{ color: "#94a3b8" }} iconType="rect" />
                <Bar yAxisId="left" dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} name="Issues" />
                <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke="#f59e0b" strokeWidth={3} dot={{ fill: "#f59e0b", r: 6 }} name="Cumulative %" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 bg-[#0064FF]/10 border border-[#0064FF]/30 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">Top Severity Category</div>
                <div className="font-bold text-[#0064FF]">{topImpact.count} of {topImpact.total} issues ({topImpact.pct}%)</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-400">Pareto Principle</div>
                <div className="font-bold text-[#FF6B00]">Live Jira Data</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
