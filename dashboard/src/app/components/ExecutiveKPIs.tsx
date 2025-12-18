import React from 'react';
import { Users, AlertTriangle, DollarSign, Film } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

// Mock sparkline data (last 7 days)
const generateSparklineData = (trend: 'up' | 'down' | 'stable') => {
  const base = 50;
  return Array.from({ length: 7 }, (_, i) => ({
    value: trend === 'up' ? base + i * 5 : trend === 'down' ? base - i * 5 : base + (Math.random() - 0.5) * 3
  }));
};

const kpis = [
  {
    label: 'Total Subscribers',
    value: '67.5M',
    change: '-2.3%',
    trend: 'down' as const,
    health: 'warning',
    icon: Users,
    sparklineData: generateSparklineData('down')
  },
  {
    label: 'Churn Risk Score',
    value: '7.8/10',
    change: '+1.2',
    trend: 'up' as const,
    health: 'critical',
    icon: AlertTriangle,
    sparklineData: generateSparklineData('up')
  },
  {
    label: 'Revenue at Risk',
    value: '$965M',
    change: 'Annual',
    trend: 'stable' as const,
    health: 'critical',
    icon: DollarSign,
    sparklineData: generateSparklineData('stable')
  },
  {
    label: 'Production Issues',
    value: '4 Active',
    change: '2 Critical',
    trend: 'up' as const,
    health: 'warning',
    icon: Film,
    sparklineData: generateSparklineData('up')
  }
];

const healthColors = {
  good: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
    icon: 'text-green-400',
    sparkline: '#10b981'
  },
  warning: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    icon: 'text-amber-400',
    sparkline: '#f59e0b'
  },
  critical: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    icon: 'text-red-400',
    sparkline: '#ef4444'
  }
};

export function ExecutiveKPIs() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        const colors = healthColors[kpi.health];

        return (
          <div
            key={index}
            className={`${colors.bg} ${colors.border} border rounded-xl p-5 transition-all hover:scale-105 hover:shadow-lg cursor-pointer relative overflow-hidden`}
          >
            {/* Background Glow */}
            <div className={`absolute inset-0 bg-gradient-to-br ${colors.bg} opacity-50 blur-xl`} />
            
            <div className="relative">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className={`${colors.bg} p-2.5 rounded-lg`}>
                  <Icon className={`w-5 h-5 ${colors.icon}`} />
                </div>
                <div className="text-right">
                  <div className={`text-xs font-medium ${colors.text}`}>
                    {kpi.change}
                  </div>
                </div>
              </div>

              {/* Value */}
              <div className="mb-3">
                <div className={`text-3xl font-bold ${colors.text} mb-1`}>
                  {kpi.value}
                </div>
                <div className="text-sm text-slate-400">{kpi.label}</div>
              </div>

              {/* Sparkline */}
              <div className="h-12 -mx-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={kpi.sparklineData}>
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={colors.sparkline}
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Trend Indicator */}
              <div className="mt-2 text-xs text-slate-500">
                Last 7 days trend
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
