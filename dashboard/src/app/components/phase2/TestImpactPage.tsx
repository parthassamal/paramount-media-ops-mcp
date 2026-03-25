import { useState } from "react";
import { Target, Play, Loader2, AlertCircle, CheckCircle, TrendingUp } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface ImpactedCase {
  case_id: number;
  title: string;
  impact_score: number;
  impact_reasons: string[];
  rca_history_count: number;
}

interface ImpactResult {
  deployment_id: string;
  changed_services: string[];
  total_affected_cases: number;
  high_priority_count: number;
  testrail_run_id: number | null;
  impacted_cases: ImpactedCase[];
  blast_radius: {
    total_blast_radius: number;
    all_affected: string[];
  };
}

export function TestImpactPage() {
  const [services, setServices] = useState("");
  const [deploymentId, setDeploymentId] = useState("");
  const [createRun, setCreateRun] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImpactResult | null>(null);

  const handleAnalyze = async () => {
    if (!services.trim()) {
      setError("Enter at least one service name");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const serviceList = services.split(",").map((s) => s.trim()).filter(Boolean);
      
      const response = await fetch(`${API_BASE}/api/phase2/test-impact/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          changed_services: serviceList,
          deployment_id: deploymentId || undefined,
          create_run: createRun,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-teal-500/20 to-cyan-500/20 border border-teal-500/30">
            <Target className="w-6 h-6 text-teal-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Test Impact Analysis</h2>
            <p className="text-sm text-slate-400">
              Analyze which tests are affected by a deployment before it happens
            </p>
          </div>
        </div>

        {/* Input Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              Changed Services (comma-separated)
            </label>
            <input
              type="text"
              value={services}
              onChange={(e) => setServices(e.target.value)}
              placeholder="auth-service, payment-api, streaming-cdn"
              className="w-full px-4 py-3 bg-[#0D1117] border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              Deployment ID (optional)
            </label>
            <input
              type="text"
              value={deploymentId}
              onChange={(e) => setDeploymentId(e.target.value)}
              placeholder="deploy-2026-03-25-v1.2.3"
              className="w-full px-4 py-3 bg-[#0D1117] border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-between mt-4">
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={createRun}
              onChange={(e) => setCreateRun(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-teal-500 focus:ring-teal-500"
            />
            Create TestRail run automatically
          </label>

          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Analyze Impact
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Total Affected Cases</p>
              <p className="text-3xl font-bold text-white mt-1">{result.total_affected_cases}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">High Priority</p>
              <p className="text-3xl font-bold text-red-400 mt-1">{result.high_priority_count}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Blast Radius</p>
              <p className="text-3xl font-bold text-amber-400 mt-1">
                {result.blast_radius?.total_blast_radius || result.changed_services.length}
              </p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">TestRail Run</p>
              <p className="text-xl font-bold text-teal-400 mt-1">
                {result.testrail_run_id ? `#${result.testrail_run_id}` : "—"}
              </p>
            </div>
          </div>

          {/* Impacted Cases Table */}
          <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800">
              <h3 className="font-semibold text-white">Prioritized Test Cases</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0D1117]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Case ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Title</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Impact Score</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Reasons</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">RCA History</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.impacted_cases.slice(0, 20).map((c) => (
                    <tr key={c.case_id} className="hover:bg-slate-800/30">
                      <td className="px-6 py-4 text-sm text-teal-400 font-mono">C{c.case_id}</td>
                      <td className="px-6 py-4 text-sm text-white max-w-md truncate">{c.title}</td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                c.impact_score >= 70
                                  ? "bg-red-500"
                                  : c.impact_score >= 40
                                  ? "bg-amber-500"
                                  : "bg-teal-500"
                              }`}
                              style={{ width: `${c.impact_score}%` }}
                            />
                          </div>
                          <span className="text-sm text-slate-300">{c.impact_score}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {c.impact_reasons.slice(0, 2).join(", ")}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {c.rca_history_count > 0 ? (
                          <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded-full">
                            {c.rca_history_count} RCAs
                          </span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
