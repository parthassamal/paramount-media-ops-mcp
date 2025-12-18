import React, { useEffect, useMemo, useState } from 'react';
import { Film, Clock, AlertCircle, CheckCircle, RefreshCcw, Wifi, WifiOff, ExternalLink } from 'lucide-react';
import { getProductionIssues, isMCPServerRunning, type ProductionIssue } from '../../api/mcpClient';

// Fallback mock items (used if MCP server is not available)
const productionItemsFallback = [
  {
    title: 'Yellowstone S6',
    status: 'critical',
    issue: 'Script delays - 3 weeks behind',
    impact: 'High',
    progress: 35,
    jiraUrl: undefined
  },
  {
    title: 'Star Trek: Discovery',
    status: 'delayed',
    issue: 'VFX rendering bottleneck',
    impact: 'Medium',
    progress: 67,
    jiraUrl: undefined
  },
  {
    title: '1923 Season 2',
    status: 'warning',
    issue: 'Location permit issues',
    impact: 'Medium',
    progress: 82,
    jiraUrl: undefined
  },
  {
    title: 'The Offer (New Series)',
    status: 'on-track',
    issue: 'No issues',
    impact: 'Low',
    progress: 92,
    jiraUrl: undefined
  }
];

const statusConfig = {
  critical: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    icon: AlertCircle,
    label: 'Critical'
  },
  delayed: {
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
    icon: Clock,
    label: 'Delayed'
  },
  warning: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    icon: AlertCircle,
    label: 'Warning'
  },
  'on-track': {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    icon: CheckCircle,
    label: 'On Track'
  }
};

export function ProductionTracking() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [items, setItems] = useState(productionItemsFallback);

  useEffect(() => {
    checkConnection();
  }, []);

  async function checkConnection() {
    const running = await isMCPServerRunning();
    setIsConnected(running);
    if (running) {
      fetchLive();
    }
  }

  function mapIssue(issue: ProductionIssue) {
    const severity = (issue.severity || '').toLowerCase();
    const status =
      severity === 'critical' ? 'critical' :
      severity === 'high' ? 'delayed' :
      severity === 'medium' ? 'warning' :
      'on-track';

    const delayDays = issue.delay_days ?? 0;
    const progress = Math.max(10, Math.min(95, 95 - delayDays * 8)); // quick heuristic for demo

    const title = issue.show && issue.show.trim().length > 0 ? issue.show : issue.issue_id;
    const impact = severity === 'critical' ? 'High' : severity === 'high' ? 'Medium' : 'Low';

    return {
      title,
      status,
      issue: issue.title,
      impact,
      progress,
      jiraUrl: issue.jira_url
    };
  }

  async function fetchLive() {
    setIsLoading(true);
    try {
      const res = await getProductionIssues({ limit: 8, include_pareto: false });
      if (res?.issues?.length) {
        const mapped = res.issues.slice(0, 8).map(mapIssue);
        setItems(mapped);
        setIsConnected(true);
        setLastUpdated(new Date());
      }
    } catch (e) {
      console.error('Failed to fetch production issues:', e);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }

  const stats = useMemo(() => {
    const critical = items.filter(i => i.status === 'critical').length;
    const delayed = items.filter(i => i.status === 'delayed' || i.status === 'warning').length;
    const onTrack = items.filter(i => i.status === 'on-track').length;
    return { critical, delayed, onTrack };
  }, [items]);

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-500/10 p-2 rounded-lg">
            <Film className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h2 className="font-bold text-white">Production Tracking</h2>
            <p className="text-sm text-slate-400">Active productions & issues</p>
          </div>
        </div>
        <div className="flex gap-2">
          {isConnected ? (
            <div className="flex items-center gap-1 px-3 py-1 bg-green-500/10 border border-green-500/30 rounded-full text-xs text-green-400">
              <Wifi className="w-3 h-3" />
              Live
            </div>
          ) : (
            <div className="flex items-center gap-1 px-3 py-1 bg-slate-800/60 border border-slate-700 rounded-full text-xs text-slate-400">
              <WifiOff className="w-3 h-3" />
              Mock
            </div>
          )}
          <button
            onClick={fetchLive}
            disabled={isLoading}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCcw className={`w-4 h-4 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-xs text-red-400">
            {stats.critical} Critical
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => {
          const config = statusConfig[item.status];
          const Icon = config.icon;

          return (
            <div
              key={index}
              className={`${config.bg} ${config.border} border rounded-lg p-4 transition-all hover:scale-[1.02]`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Film className={`w-4 h-4 ${config.text}`} />
                    <h3 className="font-bold text-white">{item.title}</h3>
                  </div>
                  <p className="text-sm text-slate-400">{item.issue}</p>
                </div>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg} ${config.border} border`}>
                  <Icon className={`w-3 h-3 ${config.text}`} />
                  <span className={`text-xs ${config.text}`}>{config.label}</span>
                </div>
              </div>

              <div className="mb-2">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Progress</span>
                  <span>{item.progress}%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${
                      item.status === 'critical' ? 'bg-red-500' :
                      item.status === 'delayed' ? 'bg-orange-500' :
                      item.status === 'warning' ? 'bg-amber-500' :
                      'bg-green-500'
                    } transition-all duration-500`}
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Impact: {item.impact}</span>
                <div className="flex items-center gap-3">
                  {item.jiraUrl && (
                    <a
                      href={item.jiraUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-400 hover:text-slate-200 inline-flex items-center gap-1"
                      title="Open in Jira"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Jira
                    </a>
                  )}
                  {item.status === 'critical' && (
                    <span className="text-red-400 font-medium">Action Required</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-800">
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <div className="text-2xl font-bold text-red-400">{stats.critical}</div>
            <div className="text-xs text-slate-500">Critical Issues</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-400">{stats.delayed}</div>
            <div className="text-xs text-slate-500">Delayed</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{stats.onTrack}</div>
            <div className="text-xs text-slate-500">On Track</div>
          </div>
        </div>
      </div>

      {lastUpdated && (
        <div className="mt-3 text-xs text-slate-500 text-right">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
