import React from 'react';
import { TrendingDown, Users, AlertTriangle, DollarSign } from 'lucide-react';

const metrics = [
  {
    label: 'Total Subscribers',
    value: '67.5M',
    change: '-2.3%',
    trend: 'down',
    icon: Users,
    color: 'blue'
  },
  {
    label: 'Monthly Churn Rate',
    value: '5.8%',
    change: '+0.4%',
    trend: 'down',
    icon: TrendingDown,
    color: 'red'
  },
  {
    label: 'At-Risk Subscribers',
    value: '3.2M',
    change: '+12%',
    trend: 'down',
    icon: AlertTriangle,
    color: 'amber'
  },
  {
    label: 'Revenue at Risk',
    value: '$965M',
    change: 'Annual',
    trend: 'neutral',
    icon: DollarSign,
    color: 'green'
  }
];

const colorClasses = {
  blue: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    icon: 'text-blue-400',
    text: 'text-blue-400'
  },
  red: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    icon: 'text-red-400',
    text: 'text-red-400'
  },
  amber: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    icon: 'text-amber-400',
    text: 'text-amber-400'
  },
  green: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    icon: 'text-green-400',
    text: 'text-green-400'
  }
};

export function MetricsGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        const colors = colorClasses[metric.color];
        
        return (
          <div
            key={metric.label}
            className={`${colors.bg} ${colors.border} border rounded-xl p-5 transition-all hover:scale-105`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`${colors.bg} p-2 rounded-lg`}>
                <Icon className={`w-5 h-5 ${colors.icon}`} />
              </div>
              {metric.trend !== 'neutral' && (
                <span className={`text-sm ${metric.trend === 'down' ? 'text-red-400' : 'text-green-400'}`}>
                  {metric.change}
                </span>
              )}
            </div>
            <div>
              <div className={`text-3xl font-bold mb-1 ${colors.text}`}>
                {metric.value}
              </div>
              <div className="text-sm text-slate-400">{metric.label}</div>
              {metric.trend === 'neutral' && (
                <div className="text-xs text-slate-500 mt-1">{metric.change}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
