import React from 'react';
import { Film, Clock, AlertCircle, CheckCircle } from 'lucide-react';

const productionItems = [
  {
    title: 'Yellowstone S6',
    status: 'critical',
    issue: 'Script delays - 3 weeks behind',
    impact: 'High',
    progress: 35
  },
  {
    title: 'Star Trek: Discovery',
    status: 'delayed',
    issue: 'VFX rendering bottleneck',
    impact: 'Medium',
    progress: 67
  },
  {
    title: '1923 Season 2',
    status: 'warning',
    issue: 'Location permit issues',
    impact: 'Medium',
    progress: 82
  },
  {
    title: 'The Offer (New Series)',
    status: 'on-track',
    issue: 'No issues',
    impact: 'Low',
    progress: 92
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
          <div className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-xs text-red-400">
            2 Critical
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {productionItems.map((item, index) => {
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
                {item.status === 'critical' && (
                  <span className="text-red-400 font-medium">Action Required</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-800">
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <div className="text-2xl font-bold text-red-400">2</div>
            <div className="text-xs text-slate-500">Critical Issues</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-400">2</div>
            <div className="text-xs text-slate-500">Delayed</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">1</div>
            <div className="text-xs text-slate-500">On Track</div>
          </div>
        </div>
      </div>
    </div>
  );
}
