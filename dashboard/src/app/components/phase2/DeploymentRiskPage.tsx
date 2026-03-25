import { useState } from "react";
import { TrendingUp, Play, Loader2, AlertCircle, Shield, AlertTriangle, XCircle, CheckCircle } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface RiskFactor {
  name: string;
  weight: number;
  value: number;
  score: number;
  details: string;
}

interface RiskResult {
  deployment_id: string;
  changed_services: string[];
  score: number;
  tier: string;
  recommendation: string;
  factors: RiskFactor[];
  blocking_conditions: string[];
  impact_analysis: {
    total_affected_cases: number;
    high_priority_count: number;
    recommended_run_id: number | null;
  };
}

const TIER_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof CheckCircle }> = {
  low: { label: "Low Risk", color: "text-green-400", bg: "bg-green-500/20 border-green-500/30", icon: CheckCircle },
  medium: { label: "Medium Risk", color: "text-amber-400", bg: "bg-amber-500/20 border-amber-500/30", icon: AlertTriangle },
  high: { label: "High Risk", color: "text-orange-400", bg: "bg-orange-500/20 border-orange-500/30", icon: AlertCircle },
  hold: { label: "HOLD", color: "text-red-400", bg: "bg-red-500/20 border-red-500/30", icon: XCircle },
};

export function DeploymentRiskPage() {
  const [services, setServices] = useState("");
  const [deploymentId, setDeploymentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RiskResult | null>(null);

  const handleScore = async () => {
    if (!services.trim()) {
      setError("Enter at least one service name");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const serviceList = services.split(",").map((s) => s.trim()).filter(Boolean);
      
      const response = await fetch(`${API_BASE}/api/phase2/deployment-risk/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          changed_services: serviceList,
          deployment_id: deploymentId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Risk scoring failed");
    } finally {
      setLoading(false);
    }
  };

  const tierConfig = result ? TIER_CONFIG[result.tier] || TIER_CONFIG.medium : null;
  const TierIcon = tierConfig?.icon || Shield;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500/20 to-blue-500/20 border border-indigo-500/30">
            <TrendingUp className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Deployment Risk Score</h2>
            <p className="text-sm text-slate-400">
              Compute composite risk score for deployment gating (0-100)
            </p>
          </div>
        </div>

        {/* Input Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">
              Services Being Deployed (comma-separated)
            </label>
            <input
              type="text"
              value={services}
              onChange={(e) => setServices(e.target.value)}
              placeholder="auth-service, payment-api, streaming-cdn"
              className="w-full px-4 py-3 bg-[#0D1117] border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
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
              className="w-full px-4 py-3 bg-[#0D1117] border border-slate-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex justify-end mt-4">
          <button
            onClick={handleScore}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-500 hover:from-indigo-600 hover:to-blue-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Calculate Risk
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
      {result && tierConfig && (
        <>
          {/* Risk Score Display */}
          <div className={`rounded-xl border-2 ${tierConfig.bg} p-8`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className={`p-4 rounded-2xl ${tierConfig.bg}`}>
                  <TierIcon className={`w-12 h-12 ${tierConfig.color}`} />
                </div>
                <div>
                  <div className="flex items-baseline gap-3">
                    <span className={`text-6xl font-bold ${tierConfig.color}`}>{result.score}</span>
                    <span className="text-2xl text-slate-400">/100</span>
                  </div>
                  <p className={`text-xl font-semibold ${tierConfig.color} mt-1`}>{tierConfig.label}</p>
                </div>
              </div>
              <div className="text-right max-w-md">
                <p className="text-sm text-slate-400 mb-2">Recommendation</p>
                <p className="text-white">{result.recommendation}</p>
              </div>
            </div>
          </div>

          {/* Blocking Conditions */}
          {result.blocking_conditions.length > 0 && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <h4 className="font-semibold text-red-400 mb-2">Blocking Conditions</h4>
              <ul className="space-y-1">
                {result.blocking_conditions.map((condition, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-slate-300">
                    <XCircle className="w-4 h-4 text-red-400" />
                    {condition}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risk Factors */}
          <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
            <h3 className="font-semibold text-white mb-4">Risk Factor Breakdown</h3>
            <div className="space-y-4">
              {result.factors.map((factor) => (
                <div key={factor.name} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">{factor.name}</span>
                      <span className="text-xs text-slate-500">({(factor.weight * 100).toFixed(0)}% weight)</span>
                    </div>
                    <span className="text-sm text-slate-300">{factor.score.toFixed(1)} pts</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          factor.score >= 20 ? "bg-red-500" : factor.score >= 10 ? "bg-amber-500" : "bg-green-500"
                        }`}
                        style={{ width: `${Math.min(factor.score / (factor.weight * 100) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-400 w-48 truncate">{factor.details}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Impact Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Affected Test Cases</p>
              <p className="text-2xl font-bold text-white mt-1">{result.impact_analysis.total_affected_cases}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">High Priority Cases</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{result.impact_analysis.high_priority_count}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Recommended TestRail Run</p>
              <p className="text-2xl font-bold text-indigo-400 mt-1">
                {result.impact_analysis.recommended_run_id ? `#${result.impact_analysis.recommended_run_id}` : "—"}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
