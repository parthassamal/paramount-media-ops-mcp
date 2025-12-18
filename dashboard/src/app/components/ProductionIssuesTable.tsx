import React from 'react';
import { Film, ExternalLink, Clock, DollarSign } from 'lucide-react';

const productionIssues = [
  {
    severity: 'critical',
    showName: 'Yellowstone Season 6',
    costImpact: '$15.2M',
    daysDelayed: 21,
    status: 'Script delays - writer negotiations',
    jiraLink: 'PROD-2847',
    department: 'Production',
    deadline: '2025-03-15'
  },
  {
    severity: 'critical',
    showName: 'Star Trek: Discovery (Final Season)',
    costImpact: '$8.7M',
    daysDelayed: 14,
    status: 'VFX rendering bottleneck',
    jiraLink: 'PROD-2891',
    department: 'Post-Production',
    deadline: '2025-02-28'
  },
  {
    severity: 'high',
    showName: '1923 Season 2',
    costImpact: '$4.3M',
    daysDelayed: 9,
    status: 'Location permit issues - Montana',
    jiraLink: 'PROD-2903',
    department: 'Production',
    deadline: '2025-04-10'
  },
  {
    severity: 'high',
    showName: 'Mayor of Kingstown S4',
    costImpact: '$3.1M',
    daysDelayed: 7,
    status: 'Cast scheduling conflicts',
    jiraLink: 'PROD-2915',
    department: 'Production',
    deadline: '2025-05-01'
  },
  {
    severity: 'medium',
    showName: 'Special Ops: Lioness S2',
    costImpact: '$1.9M',
    daysDelayed: 5,
    status: 'Weather delays - outdoor shoots',
    jiraLink: 'PROD-2928',
    department: 'Production',
    deadline: '2025-06-15'
  },
  {
    severity: 'medium',
    showName: 'The Offer - New Series',
    costImpact: '$0.8M',
    daysDelayed: 2,
    status: 'Minor equipment issues',
    jiraLink: 'PROD-2934',
    department: 'Production',
    deadline: '2025-07-01'
  }
];

const severityConfig = {
  critical: {
    dot: '🔴',
    bg: 'bg-red-500/10',
    text: 'text-red-400',
    border: 'border-red-500/30'
  },
  high: {
    dot: '🟡',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30'
  },
  medium: {
    dot: '🟢',
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    border: 'border-green-500/30'
  }
};

export function ProductionIssuesTable() {
  const handleRowClick = (jiraLink: string) => {
    // Mock JIRA link
    alert(`Opening JIRA ticket: ${jiraLink}\nURL: https://paramount.atlassian.net/browse/${jiraLink}`);
  };

  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-[#0064FF]/10 p-2 rounded-lg">
            <Film className="w-5 h-5 text-[#0064FF]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Production Issues Tracker</h2>
            <p className="text-sm text-slate-400">Active delays and cost impacts</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-xs text-red-400 font-medium">
            2 Critical
          </div>
          <div className="px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full text-xs text-amber-400 font-medium">
            2 High Priority
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Severity
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Show Name
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Status
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Cost Impact
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Days Delayed
              </th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Department
              </th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody>
            {productionIssues.map((issue, index) => {
              const config = severityConfig[issue.severity];

              return (
                <tr
                  key={index}
                  onClick={() => handleRowClick(issue.jiraLink)}
                  className={`border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors group`}
                >
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{config.dot}</span>
                      <span className={`text-xs font-medium ${config.text} capitalize`}>
                        {issue.severity}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <Film className="w-4 h-4 text-slate-500" />
                      <span className="font-medium text-white">{issue.showName}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-sm text-slate-400">{issue.status}</span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <DollarSign className="w-4 h-4 text-red-400" />
                      <span className="font-bold text-red-400">{issue.costImpact}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Clock className="w-4 h-4 text-amber-400" />
                      <span className="font-bold text-amber-400">{issue.daysDelayed}d</span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-sm text-slate-400">{issue.department}</span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <button
                      className="inline-flex items-center gap-1 px-3 py-1 bg-[#0064FF]/10 border border-[#0064FF]/30 rounded-lg text-xs font-medium text-[#0064FF] hover:bg-[#0064FF]/20 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRowClick(issue.jiraLink);
                      }}
                    >
                      {issue.jiraLink}
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="mt-6 pt-6 border-t border-slate-800">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-red-400">$33.2M</div>
            <div className="text-xs text-slate-500">Total Cost Impact</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-400">58 Days</div>
            <div className="text-xs text-slate-500">Total Delays</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-[#0064FF]">6 Shows</div>
            <div className="text-xs text-slate-500">Affected Productions</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">42%</div>
            <div className="text-xs text-slate-500">Resolution Rate</div>
          </div>
        </div>
      </div>
    </div>
  );
}
