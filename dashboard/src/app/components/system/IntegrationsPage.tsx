import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  ServerCog,
  XCircle,
} from "lucide-react";
import { API_BASE } from "../../../config/api";

type IntegrationCard = {
  key: string;
  label: string;
  endpoint: string;
  statusField?: string;
};

type ObservabilityConfig = {
  observability_source: string;
  newrelic_enabled: boolean;
  newrelic_configured: boolean;
  datadog_enabled: boolean;
  datadog_configured: boolean;
  testrail_configured: boolean;
  local_llm_configured: boolean;
};

const INTEGRATION_ENDPOINTS: IntegrationCard[] = [
  { key: "jira", label: "Jira", endpoint: "/api/jira/health", statusField: "status" },
  { key: "confluence", label: "Confluence", endpoint: "/api/confluence/health", statusField: "status" },
  { key: "streaming", label: "Streaming (Conviva/New Relic)", endpoint: "/api/streaming/health" },
  { key: "analytics", label: "Analytics", endpoint: "/api/analytics/health", statusField: "status" },
  { key: "adobe", label: "Adobe Export", endpoint: "/adobe/health", statusField: "status" },
  { key: "ai", label: "AI Services", endpoint: "/api/ai/health", statusField: "status" },
  { key: "pipeline", label: "RCA Pipeline", endpoint: "/api/rca/health", statusField: "status" },
];

export function IntegrationsPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systemHealth, setSystemHealth] = useState<Record<string, any> | null>(null);
  const [observability, setObservability] = useState<ObservabilityConfig | null>(null);
  const [integrationResponses, setIntegrationResponses] = useState<Record<string, any>>({});

  const fetchAll = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const requests = [
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/api/rca/config/observability`),
        ...INTEGRATION_ENDPOINTS.map((item) => fetch(`${API_BASE}${item.endpoint}`)),
      ];

      const responses = await Promise.all(requests);
      const [healthRes, observabilityRes, ...integrationRes] = responses;

      if (!healthRes.ok) {
        throw new Error("Failed to load platform health");
      }
      const healthData = await healthRes.json();
      setSystemHealth(healthData);

      if (observabilityRes.ok) {
        setObservability(await observabilityRes.json());
      } else {
        setObservability(null);
      }

      const mapped: Record<string, any> = {};
      for (let i = 0; i < INTEGRATION_ENDPOINTS.length; i += 1) {
        const item = INTEGRATION_ENDPOINTS[i];
        const response = integrationRes[i];
        if (!response.ok) {
          mapped[item.key] = { __http_error: response.status };
          continue;
        }
        mapped[item.key] = await response.json();
      }
      setIntegrationResponses(mapped);
    } catch (err: any) {
      setError(err?.message || "Failed to load integrations");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/30">
              <ServerCog className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Integrations</h2>
              <p className="text-sm text-slate-400">
                Live integration health and configuration status
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchAll(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors disabled:opacity-60"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
          <p className="text-xs text-slate-500 uppercase">Platform Status</p>
          <p className="text-lg text-green-400 font-semibold mt-1">
            {systemHealth?.data?.status || "unknown"}
          </p>
        </div>
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
          <p className="text-xs text-slate-500 uppercase">Mock Mode</p>
          <p className="text-lg text-slate-200 font-semibold mt-1">
            {String(systemHealth?.data?.mock_mode ?? "unknown")}
          </p>
        </div>
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
          <p className="text-xs text-slate-500 uppercase">Observability Source</p>
          <p className="text-lg text-blue-300 font-semibold mt-1">
            {observability?.observability_source || "unknown"}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {INTEGRATION_ENDPOINTS.map((item) => {
          const data = integrationResponses[item.key];
          const httpError = data?.__http_error;
          const derived = item.statusField ? data?.[item.statusField] : data?.status;
          const status = httpError ? "error" : String(derived || "unknown").toLowerCase();
          const healthy = ["healthy", "live", "operational"].includes(status);
          const disabled = status === "disabled";

          return (
            <div key={item.key} className="bg-[#161B22] rounded-xl border border-slate-800 p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-300">{item.label}</p>
                {httpError ? (
                  <XCircle className="w-4 h-4 text-red-400" />
                ) : healthy ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                ) : (
                  <AlertCircle className={`w-4 h-4 ${disabled ? "text-slate-500" : "text-amber-400"}`} />
                )}
              </div>
              <p
                className={`mt-2 text-sm font-medium ${
                  httpError
                    ? "text-red-400"
                    : healthy
                    ? "text-green-400"
                    : disabled
                    ? "text-slate-400"
                    : "text-amber-400"
                }`}
              >
                {httpError ? `HTTP ${httpError}` : status}
              </p>
              <p className="mt-2 text-xs text-slate-500 break-all">{item.endpoint}</p>
            </div>
          );
        })}
      </div>

      {observability && (
        <div className="bg-[#161B22] rounded-xl border border-slate-800 p-6">
          <h3 className="text-white font-semibold mb-4">Observability Config</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 text-sm">
            <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3">
              <p className="text-slate-500">New Relic Enabled</p>
              <p className="text-slate-200 mt-1">{String(observability.newrelic_enabled)}</p>
            </div>
            <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3">
              <p className="text-slate-500">New Relic Configured</p>
              <p className="text-slate-200 mt-1">{String(observability.newrelic_configured)}</p>
            </div>
            <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3">
              <p className="text-slate-500">Datadog Enabled</p>
              <p className="text-slate-200 mt-1">{String(observability.datadog_enabled)}</p>
            </div>
            <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3">
              <p className="text-slate-500">Datadog Configured</p>
              <p className="text-slate-200 mt-1">{String(observability.datadog_configured)}</p>
            </div>
            <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3">
              <p className="text-slate-500">TestRail Configured</p>
              <p className="text-slate-200 mt-1">{String(observability.testrail_configured)}</p>
            </div>
            <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3">
              <p className="text-slate-500">Local LLM Configured</p>
              <p className="text-slate-200 mt-1">{String(observability.local_llm_configured)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
