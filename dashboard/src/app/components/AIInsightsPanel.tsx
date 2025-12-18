import React from 'react';
import { Sparkles, TrendingUp, AlertCircle, Lightbulb } from 'lucide-react';

const insights = [
  {
    priority: 'critical',
    icon: AlertCircle,
    title: 'Churn Concentration Alert',
    description: '80% of churn originates from 20% of content genres → Immediate focus needed on Reality TV and Sports content',
    action: 'Launch targeted retention campaign',
    impact: '$425M potential recovery'
  },
  {
    priority: 'high',
    icon: TrendingUp,
    title: 'Price-Sensitive Cohort Opportunity',
    description: 'Millennials show 34% higher engagement with ad-supported tier → Expand AVOD offerings',
    action: 'Create hybrid pricing tiers',
    impact: '$288M ARR opportunity'
  },
  {
    priority: 'high',
    icon: Lightbulb,
    title: 'Streaming QoE Degradation',
    description: 'Buffering ratio increased 45% during peak hours (8-11 PM) → CDN optimization required',
    action: 'Scale edge servers in top 5 metros',
    impact: '15% churn reduction'
  },
  {
    priority: 'medium',
    icon: Sparkles,
    title: 'Production Pipeline Insight',
    description: 'VFX delays correlate with 28% subscriber disappointment → AI-assisted rendering could accelerate by 40%',
    action: 'Deploy ML-based VFX pipeline',
    impact: '3-week faster delivery'
  }
];

const priorityConfig = {
  critical: {
    bg: 'bg-red-500/20',
    border: 'border-red-500/50',
    text: 'text-red-400',
    badge: 'bg-red-500',
    label: 'CRITICAL'
  },
  high: {
    bg: 'bg-amber-500/20',
    border: 'border-amber-500/50',
    text: 'text-amber-400',
    badge: 'bg-amber-500',
    label: 'HIGH'
  },
  medium: {
    bg: 'bg-blue-500/20',
    border: 'border-blue-500/50',
    text: 'text-blue-400',
    badge: 'bg-blue-500',
    label: 'MEDIUM'
  }
};

export function AIInsightsPanel() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-700/50 shadow-2xl">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0064FF]/20 via-purple-600/20 to-[#0064FF]/20 opacity-50" />
      <div className="absolute inset-0 bg-[#0D1117]/80 backdrop-blur-sm" />
      
      {/* Content */}
      <div className="relative p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#0064FF] to-purple-600 rounded-xl blur-lg opacity-50 animate-pulse" />
              <div className="relative bg-gradient-to-r from-[#0064FF] to-purple-600 p-3 rounded-xl">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">AI-Powered Insights</h2>
              <p className="text-sm text-slate-400">Actionable recommendations from predictive analytics</p>
            </div>
          </div>
          <div className="px-3 py-1 bg-gradient-to-r from-[#0064FF] to-purple-600 rounded-full">
            <span className="text-xs font-bold text-white">ML Model v3.2</span>
          </div>
        </div>

        {/* Insights Grid */}
        <div className="space-y-4">
          {insights.map((insight, index) => {
            const Icon = insight.icon;
            const config = priorityConfig[insight.priority];

            return (
              <div
                key={index}
                className={`${config.bg} ${config.border} border rounded-xl p-5 transition-all hover:scale-[1.02] hover:shadow-lg cursor-pointer group`}
              >
                <div className="flex items-start gap-4">
                  <div className={`${config.bg} p-3 rounded-lg flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${config.text}`} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-bold text-white group-hover:text-[#0064FF] transition-colors">
                        {insight.title}
                      </h3>
                      <span className={`${config.badge} px-2 py-0.5 rounded text-xs font-bold text-white`}>
                        {config.label}
                      </span>
                    </div>
                    
                    <p className="text-sm text-slate-300 mb-3 leading-relaxed">
                      {insight.description}
                    </p>
                    
                    <div className="flex items-center justify-between gap-4 pt-3 border-t border-slate-700/50">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">Recommended Action:</span>
                        <span className="text-xs font-medium text-[#0064FF]">{insight.action}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-green-400" />
                        <span className="text-xs font-bold text-green-400">{insight.impact}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Stats */}
        <div className="mt-6 pt-6 border-t border-slate-700/50">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-[#0064FF]">4</div>
              <div className="text-xs text-slate-500">Active Insights</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-400">$728M</div>
              <div className="text-xs text-slate-500">Total Opportunity</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">94%</div>
              <div className="text-xs text-slate-500">Model Accuracy</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
