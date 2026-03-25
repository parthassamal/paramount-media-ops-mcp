import { useState, useEffect } from "react";
import { Zap, Play, Loader2, AlertCircle, TrendingUp, TrendingDown, Target, CheckCircle, XCircle } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface PerformerCase {
  case_id: number;
  title: string;
  effectiveness_score: number;
  true_positives?: number;
  false_positives?: number;
  missed_detections?: number;
  total_runs?: number;
  recommendation?: string;
}

interface EffectivenessResult {
  total_cases: number;
  average_effectiveness: number;
  top_performers: PerformerCase[];
  underperformers: PerformerCase[];
  recommendations: string[];
}

interface TrendsResult {
  period_days: number;
  true_positives: number;
  false_positives: number;
  missed_detections: number;
  total_correlations: number;
  precision: number | null;
  recall: number | null;
}

export function EffectivenessPage() {
  const [loading, setLoading] = useState(false);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EffectivenessResult | null>(null);
  const [trends, setTrends] = useState<TrendsResult | null>(null);
  const [view, setView] = useState<"top" | "under">("top");

  useEffect(() => {
    fetchTrends();
  }, []);

  const fetchTrends = async () => {
    setLoadingTrends(true);
    try {
      const response = await fetch(`${API_BASE}/api/phase2/effectiveness/trends?days=30`);
      if (response.ok) {
        const data = await response.json();
        setTrends(data);
      }
    } catch (err) {
      // Trends not available is okay
    } finally {
      setLoadingTrends(false);
    }
  };

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/phase2/effectiveness/calculate`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      fetchTrends();
    } catch (err: any) {
      setError(err.message || "Calculation failed");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400";
    if (score >= 50) return "text-amber-400";
    return "text-red-400";
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return "bg-green-500";
    if (score >= 50) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30">
              <Zap className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Test Effectiveness Scoring</h2>
              <p className="text-sm text-slate-400">
                Track true positives, false positives, and missed detections per test case
              </p>
            </div>
          </div>

          <button
            onClick={handleCalculate}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Calculate Scores
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {/* Trends Summary */}
      {!loadingTrends && trends && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <p className="text-sm text-slate-400">Period</p>
            <p className="text-2xl font-bold text-white mt-1">{trends.period_days}d</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-green-500/30 p-4">
            <div className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <p className="text-sm text-green-400">True Positives</p>
            </div>
            <p className="text-2xl font-bold text-green-400 mt-1">{trends.true_positives}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-amber-500/30 p-4">
            <div className="flex items-center gap-1">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <p className="text-sm text-amber-400">False Positives</p>
            </div>
            <p className="text-2xl font-bold text-amber-400 mt-1">{trends.false_positives}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-red-500/30 p-4">
            <div className="flex items-center gap-1">
              <XCircle className="w-4 h-4 text-red-400" />
              <p className="text-sm text-red-400">Missed</p>
            </div>
            <p className="text-2xl font-bold text-red-400 mt-1">{trends.missed_detections}</p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <div className="flex items-center gap-1">
              <Target className="w-4 h-4 text-blue-400" />
              <p className="text-sm text-slate-400">Precision</p>
            </div>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {trends.precision !== null ? `${(trends.precision * 100).toFixed(0)}%` : "—"}
            </p>
          </div>
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
            <div className="flex items-center gap-1">
              <Target className="w-4 h-4 text-purple-400" />
              <p className="text-sm text-slate-400">Recall</p>
            </div>
            <p className="text-2xl font-bold text-purple-400 mt-1">
              {trends.recall !== null ? `${(trends.recall * 100).toFixed(0)}%` : "—"}
            </p>
          </div>
        </div>
      )}

      {result ? (
        <>
          {/* Overall Score */}
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Suite Average Effectiveness</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className={`text-5xl font-bold ${getScoreColor(result.average_effectiveness)}`}>
                    {result.average_effectiveness}
                  </span>
                  <span className="text-xl text-slate-400">/100</span>
                </div>
              </div>
              <div className="w-64">
                <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${getScoreBg(result.average_effectiveness)}`}
                    style={{ width: `${result.average_effectiveness}%` }}
                  />
                </div>
                <p className="text-sm text-slate-400 mt-2 text-right">
                  {result.total_cases} cases analyzed
                </p>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
              <h4 className="font-semibold text-emerald-400 mb-3">Recommendations</h4>
              <ul className="space-y-2">
                {result.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                    <Zap className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Toggle View */}
          <div className="flex gap-2">
            <button
              onClick={() => setView("top")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                view === "top"
                  ? "bg-green-500/20 text-green-400 border border-green-500/30"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Top Performers ({result.top_performers.length})
            </button>
            <button
              onClick={() => setView("under")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                view === "under"
                  ? "bg-red-500/20 text-red-400 border border-red-500/30"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <TrendingDown className="w-4 h-4" />
              Underperformers ({result.underperformers.length})
            </button>
          </div>

          {/* Cases Table */}
          <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800">
              <h3 className="font-semibold text-white">
                {view === "top" ? "Top Performing Tests" : "Underperforming Tests"}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0D1117]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Case</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Title</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Score</th>
                    {view === "top" ? (
                      <>
                        <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">True Pos</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Total Runs</th>
                      </>
                    ) : (
                      <>
                        <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">False Pos</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Missed</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Recommendation</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {(view === "top" ? result.top_performers : result.underperformers).map((c) => (
                    <tr key={c.case_id} className="hover:bg-slate-800/30">
                      <td className="px-6 py-4 text-sm text-emerald-400 font-mono">C{c.case_id}</td>
                      <td className="px-6 py-4 text-sm text-white max-w-xs truncate">{c.title}</td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-12 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${getScoreBg(c.effectiveness_score)}`}
                              style={{ width: `${c.effectiveness_score}%` }}
                            />
                          </div>
                          <span className={`text-sm font-medium ${getScoreColor(c.effectiveness_score)}`}>
                            {c.effectiveness_score.toFixed(0)}
                          </span>
                        </div>
                      </td>
                      {view === "top" ? (
                        <>
                          <td className="px-6 py-4 text-center text-sm text-green-400">{c.true_positives}</td>
                          <td className="px-6 py-4 text-center text-sm text-slate-400">{c.total_runs}</td>
                        </>
                      ) : (
                        <>
                          <td className="px-6 py-4 text-center text-sm text-amber-400">{c.false_positives}</td>
                          <td className="px-6 py-4 text-center text-sm text-red-400">{c.missed_detections}</td>
                          <td className="px-6 py-4 text-xs text-slate-400 max-w-xs truncate">{c.recommendation}</td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-12 text-center">
          <Zap className="w-12 h-12 text-emerald-500/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No Effectiveness Data</h3>
          <p className="text-slate-400 mb-4">Calculate scores to analyze test effectiveness over time</p>
        </div>
      )}
    </div>
  );
}
