import { useState, useEffect } from "react";
import { Sparkles, Play, Loader2, AlertCircle, Trash2, AlertTriangle, Copy, FileX, Search } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface HygieneIssue {
  issue_type: string;
  case_id: number;
  title: string;
  severity: string;
  details: string;
  recommended_action: string;
  related_case_id?: number;
}

interface HygieneReport {
  report_id: string;
  generated_at: string;
  suite_id: number;
  total_cases: number;
  total_issues: number;
  issues: HygieneIssue[];
  summary: Record<string, number>;
}

const ISSUE_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof AlertCircle }> = {
  stale: { label: "Stale", color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/30", icon: FileX },
  flaky: { label: "Flaky", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30", icon: AlertTriangle },
  duplicate: { label: "Duplicate", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/30", icon: Copy },
  orphaned_refs: { label: "Orphaned", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/30", icon: Search },
  unverified_generated: { label: "Unverified", color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/30", icon: AlertCircle },
  coverage_gap: { label: "Coverage Gap", color: "text-red-400", bg: "bg-red-500/10 border-red-500/30", icon: Trash2 },
};

export function SuiteHygienePage() {
  const [loading, setLoading] = useState(false);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<HygieneReport | null>(null);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    fetchLatestReport();
  }, []);

  const fetchLatestReport = async () => {
    setLoadingLatest(true);
    try {
      const response = await fetch(`${API_BASE}/api/phase2/suite-hygiene/latest`);
      if (response.ok) {
        const data = await response.json();
        setReport(data);
      }
    } catch (err) {
      // No existing report is okay
    } finally {
      setLoadingLatest(false);
    }
  };

  const handleRunCheck = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/phase2/suite-hygiene/run`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setReport(data);
    } catch (err: any) {
      setError(err.message || "Hygiene check failed");
    } finally {
      setLoading(false);
    }
  };

  const filteredIssues = report?.issues.filter(
    (i) => filter === "all" || i.issue_type === filter
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
              <Sparkles className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Suite Hygiene</h2>
              <p className="text-sm text-slate-400">
                Find stale, flaky, duplicate, orphaned, and unverified test cases
              </p>
            </div>
          </div>

          <button
            onClick={handleRunCheck}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Hygiene Check
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {loadingLatest ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
        </div>
      ) : report ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Total Cases</p>
              <p className="text-2xl font-bold text-white mt-1">{report.total_cases}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-red-500/30 p-4">
              <p className="text-sm text-slate-400">Issues Found</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{report.total_issues}</p>
            </div>
            {Object.entries(ISSUE_CONFIG).map(([key, config]) => (
              <div key={key} className={`bg-[#161B22] rounded-xl border ${config.bg.split(" ")[1]} p-4`}>
                <p className={`text-sm ${config.color}`}>{config.label}</p>
                <p className={`text-2xl font-bold ${config.color} mt-1`}>{report.summary[key] || 0}</p>
              </div>
            ))}
          </div>

          {/* Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === "all"
                  ? "bg-purple-500 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              All ({report.total_issues})
            </button>
            {Object.entries(ISSUE_CONFIG).map(([key, config]) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === key
                    ? `${config.bg.split(" ")[0]} ${config.color} border ${config.bg.split(" ")[1]}`
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {config.label} ({report.summary[key] || 0})
              </button>
            ))}
          </div>

          {/* Issues Table */}
          <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-semibold text-white">Hygiene Issues</h3>
              <span className="text-sm text-slate-400">
                Report: {report.report_id} • {new Date(report.generated_at).toLocaleString()}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0D1117]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Case ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Title</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Severity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Details</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredIssues.slice(0, 50).map((issue, idx) => {
                    const config = ISSUE_CONFIG[issue.issue_type] || ISSUE_CONFIG.stale;
                    const Icon = config.icon;
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${config.bg}`}>
                            <Icon className={`w-3 h-3 ${config.color}`} />
                            <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-purple-400 font-mono">
                          {issue.case_id > 0 ? `C${issue.case_id}` : "—"}
                        </td>
                        <td className="px-6 py-4 text-sm text-white max-w-xs truncate">{issue.title}</td>
                        <td className="px-6 py-4 text-center">
                          <span className={`text-xs font-medium px-2 py-1 rounded ${
                            issue.severity === "high"
                              ? "bg-red-500/10 text-red-400"
                              : issue.severity === "medium"
                              ? "bg-amber-500/10 text-amber-400"
                              : "bg-slate-500/10 text-slate-400"
                          }`}>
                            {issue.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-400 max-w-xs truncate">{issue.details}</td>
                        <td className="px-6 py-4 text-xs text-slate-300">{issue.recommended_action}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-12 text-center">
          <Sparkles className="w-12 h-12 text-purple-500/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No Hygiene Report</h3>
          <p className="text-slate-400 mb-4">Run a hygiene check to scan your test suite for issues</p>
        </div>
      )}
    </div>
  );
}
