import { useState, useEffect } from "react";
import { Bell, Play, Loader2, AlertCircle, CheckCircle, XCircle, Zap } from "lucide-react";
import { API_BASE } from "../../../config/api";

interface CoverageGap {
  alert_id: string;
  alert_name: string;
  source: string;
  service: string;
  metric: string;
  threshold: string;
  duration: string;
}

interface CoverageResult {
  total_alerts: number;
  covered: number;
  coverage_rate: number;
  covered_details: { alert_id: string; alert_name: string; matched_case_id: number; matched_case_title: string }[];
  gaps: CoverageGap[];
}

interface GeneratedCase {
  title: string;
  type: string;
  priority: string;
  preconditions: string;
  steps: { action: string; expected: string }[];
}

interface GenerationResult {
  generated_cases: GeneratedCase[];
  queued_for_review: boolean;
  review_id?: string;
  message?: string;
}

export function AlertTestsPage() {
  const [loadingCoverage, setLoadingCoverage] = useState(true);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coverage, setCoverage] = useState<CoverageResult | null>(null);
  const [generated, setGenerated] = useState<GenerationResult | null>(null);
  const [selectedGaps, setSelectedGaps] = useState<string[]>([]);

  useEffect(() => {
    fetchCoverage();
  }, []);

  const fetchCoverage = async () => {
    setLoadingCoverage(true);
    try {
      const response = await fetch(`${API_BASE}/api/phase2/alert-tests/coverage`);
      if (response.ok) {
        const data = await response.json();
        setCoverage(data);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoadingCoverage(false);
    }
  };

  const handleGenerate = async () => {
    setLoadingGenerate(true);
    setError(null);
    setGenerated(null);

    try {
      const response = await fetch(`${API_BASE}/api/phase2/alert-tests/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alert_ids: selectedGaps.length > 0 ? selectedGaps : null,
          auto_queue: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setGenerated(data);
      
      // Refresh coverage
      fetchCoverage();
    } catch (err: any) {
      setError(err.message || "Generation failed");
    } finally {
      setLoadingGenerate(false);
    }
  };

  const toggleGap = (alertId: string) => {
    setSelectedGaps((prev) =>
      prev.includes(alertId) ? prev.filter((id) => id !== alertId) : [...prev, alertId]
    );
  };

  const coveragePercent = coverage ? Math.round(coverage.coverage_rate * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border border-yellow-500/30">
              <Bell className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Alert-Driven Test Generation</h2>
              <p className="text-sm text-slate-400">
                Generate test cases from monitoring alert definitions
              </p>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loadingGenerate}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-medium rounded-lg transition-all disabled:opacity-50"
          >
            {loadingGenerate ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            Generate Tests {selectedGaps.length > 0 ? `(${selectedGaps.length})` : "for All Gaps"}
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {loadingCoverage ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-yellow-500 animate-spin" />
        </div>
      ) : coverage ? (
        <>
          {/* Coverage Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Total Alerts</p>
              <p className="text-3xl font-bold text-white mt-1">{coverage.total_alerts}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-green-500/30 p-4">
              <p className="text-sm text-slate-400">Covered</p>
              <p className="text-3xl font-bold text-green-400 mt-1">{coverage.covered}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-red-500/30 p-4">
              <p className="text-sm text-slate-400">Gaps</p>
              <p className="text-3xl font-bold text-red-400 mt-1">{coverage.gaps.length}</p>
            </div>
            <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <p className="text-sm text-slate-400">Coverage Rate</p>
              <div className="flex items-center gap-3 mt-1">
                <p className={`text-3xl font-bold ${
                  coveragePercent >= 80 ? "text-green-400" :
                  coveragePercent >= 50 ? "text-amber-400" : "text-red-400"
                }`}>
                  {coveragePercent}%
                </p>
                <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      coveragePercent >= 80 ? "bg-green-500" :
                      coveragePercent >= 50 ? "bg-amber-500" : "bg-red-500"
                    }`}
                    style={{ width: `${coveragePercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Coverage Gaps */}
          {coverage.gaps.length > 0 && (
            <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold text-white">Coverage Gaps (Alerts Without Tests)</h3>
                {selectedGaps.length > 0 && (
                  <button
                    onClick={() => setSelectedGaps([])}
                    className="text-sm text-slate-400 hover:text-white"
                  >
                    Clear Selection
                  </button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[#0D1117]">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase w-10">
                        <input
                          type="checkbox"
                          checked={selectedGaps.length === coverage.gaps.length}
                          onChange={() => {
                            if (selectedGaps.length === coverage.gaps.length) {
                              setSelectedGaps([]);
                            } else {
                              setSelectedGaps(coverage.gaps.map((g) => g.alert_id));
                            }
                          }}
                          className="w-4 h-4 rounded border-slate-600 bg-slate-800"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Source</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Alert Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Service</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Threshold</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {coverage.gaps.map((gap) => (
                      <tr
                        key={gap.alert_id}
                        className={`hover:bg-slate-800/30 cursor-pointer ${
                          selectedGaps.includes(gap.alert_id) ? "bg-yellow-500/10" : ""
                        }`}
                        onClick={() => toggleGap(gap.alert_id)}
                      >
                        <td className="px-6 py-4">
                          <input
                            type="checkbox"
                            checked={selectedGaps.includes(gap.alert_id)}
                            onChange={() => toggleGap(gap.alert_id)}
                            className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-yellow-500"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            gap.source === "newrelic"
                              ? "bg-green-500/10 text-green-400"
                              : "bg-purple-500/10 text-purple-400"
                          }`}>
                            {gap.source}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-white">{gap.alert_name}</td>
                        <td className="px-6 py-4 text-sm text-slate-400">{gap.service}</td>
                        <td className="px-6 py-4 text-sm text-amber-400 font-mono">{gap.threshold}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Generated Cases */}
          {generated && generated.generated_cases.length > 0 && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <h4 className="font-semibold text-green-400">
                  Generated {generated.generated_cases.length} Test Case(s)
                </h4>
                {generated.review_id && (
                  <span className="text-sm text-slate-400">
                    • Review ID: {generated.review_id}
                  </span>
                )}
              </div>
              <div className="space-y-3">
                {generated.generated_cases.map((tc, idx) => (
                  <div key={idx} className="bg-[#0D1117] rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        tc.type === "reliability" ? "bg-red-500/10 text-red-400" :
                        tc.type === "performance" ? "bg-amber-500/10 text-amber-400" :
                        "bg-blue-500/10 text-blue-400"
                      }`}>
                        {tc.type}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-700 text-slate-300">
                        {tc.priority}
                      </span>
                    </div>
                    <p className="text-white font-medium">{tc.title}</p>
                    <p className="text-sm text-slate-400 mt-1">{tc.preconditions}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Covered Alerts */}
          {coverage.covered_details.length > 0 && (
            <div className="bg-[#161B22] rounded-xl border border-slate-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h3 className="font-semibold text-white">Covered Alerts</h3>
              </div>
              <div className="overflow-x-auto max-h-64">
                <table className="w-full">
                  <thead className="bg-[#0D1117] sticky top-0">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Alert</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Matched Case</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {coverage.covered_details.map((c) => (
                      <tr key={c.alert_id} className="hover:bg-slate-800/30">
                        <td className="px-6 py-3 text-sm text-white">{c.alert_name}</td>
                        <td className="px-6 py-3 text-sm text-green-400">
                          C{c.matched_case_id}: {c.matched_case_title}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-12 text-center">
          <Bell className="w-12 h-12 text-yellow-500/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Unable to Load Coverage</h3>
          <p className="text-slate-400">Check that New Relic and Datadog are configured</p>
        </div>
      )}
    </div>
  );
}
