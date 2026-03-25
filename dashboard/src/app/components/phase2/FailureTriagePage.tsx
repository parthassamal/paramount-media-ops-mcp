import { useState } from "react";
import { Filter, Play, Loader2, AlertCircle, CheckCircle, XCircle, AlertTriangle, Clock } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface TriagedFailure {
  case_id: number;
  test_id: number;
  title: string;
  classification: string;
  confidence: number;
  signals: string[];
  recommended_action: string;
  rca_triggered: boolean;
}

interface TriageResult {
  run_id: number;
  total_tests: number;
  passed: number;
  failed: number;
  triaged_failures: TriagedFailure[];
  summary: Record<string, number>;
  rca_triggered: { case_id: number; title: string }[];
  actions_taken: { type: string; case_id: number; message: string }[];
}

const CLASSIFICATION_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof CheckCircle }> = {
  genuine_regression: { label: "Genuine Regression", color: "text-red-400", bg: "bg-red-500/10 border-red-500/30", icon: XCircle },
  flaky_test: { label: "Flaky Test", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30", icon: AlertTriangle },
  environment_issue: { label: "Environment Issue", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/30", icon: AlertCircle },
  known_gap: { label: "Known Gap", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/30", icon: Clock },
  stale_test: { label: "Stale Test", color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/30", icon: Clock },
  unknown: { label: "Unknown", color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/30", icon: AlertCircle },
};

export function FailureTriagePage() {
  const [runId, setRunId] = useState("");
  const [autoAction, setAutoAction] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TriageResult | null>(null);

  const handleTriage = async () => {
    if (!runId.trim()) {
      setError("Enter a TestRail run ID");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/phase2/triage/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: parseInt(runId),
          auto_action: autoAction,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Triage failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 border border-orange-500/30">
            <Filter className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Automated Failure Triage</h2>
            <p className="text-sm text-slate-400">
              Classify test failures: regression, flaky, environment, gap, or stale
            </p>
          </div>
        </div>

        {/* Input Form */}
        <div className="flex items-end gap-4 mt-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-400 mb-2">
              TestRail Run ID
            </label>
            <input
              type="number"
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
              placeholder="12345"
              className="w-full px-4 py-3 bg-[#0D1117] border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-orange-500"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer pb-3">
            <input
              type="checkbox"
              checked={autoAction}
              onChange={(e) => setAutoAction(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-orange-500 focus:ring-orange-500"
            />
            Take automated actions
          </label>

          <button
            onClick={handleTriage}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Triage Failures
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
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Total Tests</p>
              <p className="text-2xl font-bold text-white mt-1">{result.total_tests}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-green-500/30 p-4">
              <p className="text-sm text-green-400">Passed</p>
              <p className="text-2xl font-bold text-green-400 mt-1">{result.passed}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-red-500/30 p-4">
              <p className="text-sm text-red-400">Failed</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{result.failed}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-red-500/30 p-4">
              <p className="text-sm text-slate-400">Genuine Regressions</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{result.summary?.genuine_regression || 0}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-amber-500/30 p-4">
              <p className="text-sm text-slate-400">Flaky Tests</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{result.summary?.flaky_test || 0}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-blue-500/30 p-4">
              <p className="text-sm text-slate-400">Env Issues</p>
              <p className="text-2xl font-bold text-blue-400 mt-1">{result.summary?.environment_issue || 0}</p>
            </div>
          </div>

          {/* Triaged Failures Table */}
          <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800">
              <h3 className="font-semibold text-white">Triaged Failures</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0D1117]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Case</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Title</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Classification</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Confidence</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Signals</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {result.triaged_failures.map((f) => {
                    const config = CLASSIFICATION_CONFIG[f.classification] || CLASSIFICATION_CONFIG.unknown;
                    const Icon = config.icon;
                    return (
                      <tr key={f.test_id} className="hover:bg-slate-800/30">
                        <td className="px-6 py-4 text-sm text-orange-400 font-mono">C{f.case_id}</td>
                        <td className="px-6 py-4 text-sm text-white max-w-xs truncate">{f.title}</td>
                        <td className="px-6 py-4 text-center">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${config.bg}`}>
                            <Icon className={`w-3 h-3 ${config.color}`} />
                            <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-sm text-slate-300">{(f.confidence * 100).toFixed(0)}%</span>
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-400 max-w-xs truncate">
                          {f.signals.join(", ")}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-300">{f.recommended_action}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* RCA Triggered */}
          {result.rca_triggered.length > 0 && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <h4 className="font-semibold text-red-400 mb-2">RCA Triggered for {result.rca_triggered.length} case(s)</h4>
              <ul className="space-y-1">
                {result.rca_triggered.map((r) => (
                  <li key={r.case_id} className="text-sm text-slate-300">
                    • C{r.case_id}: {r.title}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
