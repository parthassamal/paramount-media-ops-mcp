import { useState, useEffect } from "react";
import { Activity, Play, Loader2, AlertCircle, Clock, GitBranch, Zap, TrendingUp, Network } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface Pattern {
  pattern_type: string;
  affected_services: string[];
  confidence_score: number;
  incident_count: number;
  description: string;
  first_seen: string;
  last_seen: string;
  actionable_insight: string;
}

interface PatternResult {
  patterns: Pattern[];
  summary: {
    total_patterns: number;
    by_type: Record<string, number>;
    high_confidence: number;
  };
  analyzed_rcas: number;
}

const PATTERN_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof Activity }> = {
  temporal_cluster: { label: "Temporal Cluster", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/30", icon: Clock },
  deployment_correlation: { label: "Deployment Correlation", color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/30", icon: GitBranch },
  service_co_failure: { label: "Co-Failure", color: "text-red-400", bg: "bg-red-500/10 border-red-500/30", icon: Network },
  recurring_root_cause: { label: "Recurring Cause", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/30", icon: Zap },
  mttr_trend: { label: "MTTR Trend", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30", icon: TrendingUp },
};

export function PatternDetectionPage() {
  const [loading, setLoading] = useState(false);
  const [loadingPatterns, setLoadingPatterns] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PatternResult | null>(null);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    fetchExistingPatterns();
  }, []);

  const fetchExistingPatterns = async () => {
    setLoadingPatterns(true);
    try {
      const response = await fetch(`${API_BASE}/api/phase2/patterns`);
      if (response.ok) {
        const patterns = await response.json();
        if (patterns.length > 0) {
          // Build result structure from existing patterns
          const byType: Record<string, number> = {};
          patterns.forEach((p: Pattern) => {
            byType[p.pattern_type] = (byType[p.pattern_type] || 0) + 1;
          });
          setResult({
            patterns,
            summary: {
              total_patterns: patterns.length,
              by_type: byType,
              high_confidence: patterns.filter((p: Pattern) => p.confidence_score >= 0.85).length,
            },
            analyzed_rcas: 0,
          });
        }
      }
    } catch (err) {
      // No patterns is okay
    } finally {
      setLoadingPatterns(false);
    }
  };

  const handleDetect = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/phase2/patterns/detect`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Pattern detection failed");
    } finally {
      setLoading(false);
    }
  };

  const filteredPatterns = result?.patterns.filter(
    (p) => filter === "all" || p.pattern_type === filter
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
              <Activity className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Cross-RCA Pattern Detection</h2>
              <p className="text-sm text-slate-400">
                Mine RCA history for temporal, deployment, co-failure, and MTTR patterns
              </p>
            </div>
          </div>

          <button
            onClick={handleDetect}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Detect Patterns
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {loadingPatterns ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
        </div>
      ) : result ? (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Total Patterns</p>
              <p className="text-2xl font-bold text-white mt-1">{result.summary.total_patterns}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-green-500/30 p-4">
              <p className="text-sm text-slate-400">High Confidence</p>
              <p className="text-2xl font-bold text-green-400 mt-1">{result.summary.high_confidence}</p>
            </div>
            {Object.entries(PATTERN_CONFIG).map(([key, config]) => (
              <div key={key} className={`bg-[#161B22] rounded-xl border ${config.bg.split(" ")[1]} p-4`}>
                <p className={`text-sm ${config.color}`}>{config.label}</p>
                <p className={`text-2xl font-bold ${config.color} mt-1`}>{result.summary.by_type[key] || 0}</p>
              </div>
            ))}
          </div>

          {/* Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === "all"
                  ? "bg-cyan-500 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              All ({result.summary.total_patterns})
            </button>
            {Object.entries(PATTERN_CONFIG).map(([key, config]) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === key
                    ? `${config.bg.split(" ")[0]} ${config.color} border ${config.bg.split(" ")[1]}`
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {config.label} ({result.summary.by_type[key] || 0})
              </button>
            ))}
          </div>

          {/* Patterns */}
          <div className="space-y-4">
            {filteredPatterns.map((pattern, idx) => {
              const config = PATTERN_CONFIG[pattern.pattern_type] || PATTERN_CONFIG.recurring_root_cause;
              const Icon = config.icon;
              return (
                <div key={idx} className={`bg-[#161B22] rounded-xl border ${config.bg.split(" ")[1]} p-6`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-xl ${config.bg}`}>
                        <Icon className={`w-6 h-6 ${config.color}`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.color}`}>
                            {config.label}
                          </span>
                          <span className="text-xs text-slate-500">
                            {pattern.incident_count} incidents
                          </span>
                        </div>
                        <p className="text-white font-medium">{pattern.description}</p>
                        <p className="text-sm text-slate-400 mt-2">
                          <span className="text-slate-500">Services:</span>{" "}
                          {pattern.affected_services.join(", ")}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-400">Confidence</span>
                        <span className={`text-lg font-bold ${
                          pattern.confidence_score >= 0.85 ? "text-green-400" :
                          pattern.confidence_score >= 0.7 ? "text-amber-400" : "text-slate-400"
                        }`}>
                          {(pattern.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700">
                    <p className="text-sm text-slate-300">
                      <span className="text-cyan-400 font-medium">Actionable Insight:</span>{" "}
                      {pattern.actionable_insight}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-12 text-center">
          <Activity className="w-12 h-12 text-cyan-500/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No Patterns Detected</h3>
          <p className="text-slate-400 mb-4">Run pattern detection to analyze your RCA history</p>
        </div>
      )}
    </div>
  );
}
