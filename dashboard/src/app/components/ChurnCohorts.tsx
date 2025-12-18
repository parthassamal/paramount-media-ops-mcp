import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Users, TrendingDown } from 'lucide-react';

const cohortData = [
  {
    name: 'High-Value Serial Churners',
    subscribers: 850000,
    impact: 425,
    risk: 'critical',
    retention: 32
  },
  {
    name: 'Price-Sensitive Millennials',
    subscribers: 720000,
    impact: 288,
    risk: 'high',
    retention: 45
  },
  {
    name: 'Content-Starved Families',
    subscribers: 540000,
    impact: 162,
    risk: 'high',
    retention: 58
  },
  {
    name: 'Platform Migration Risk',
    subscribers: 380000,
    impact: 90,
    risk: 'medium',
    retention: 67
  }
];

const COLORS = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#10b981'
};

export function ChurnCohorts() {
  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-purple-500/10 p-2 rounded-lg">
            <Users className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Top Churn Risk Cohorts</h2>
            <p className="text-sm text-slate-400">Subscriber segments by churn probability</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-lg">
          <TrendingDown className="w-4 h-4 text-red-400" />
          <span className="text-sm font-medium text-red-400">High Risk</span>
        </div>
      </div>

      <div className="h-80 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={cohortData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              type="number" 
              stroke="#94a3b8" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Subscribers', position: 'insideBottom', offset: -5, fill: '#94a3b8', fontSize: 12 }}
              tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
            />
            <YAxis 
              type="category" 
              dataKey="name" 
              stroke="#94a3b8" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              width={180}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9'
              }}
              formatter={(value: number, name: string, props: any) => {
                if (name === 'subscribers') {
                  return [
                    <div key="tooltip">
                      <div>{value.toLocaleString()} subscribers</div>
                      <div className="text-xs text-slate-400">Impact: ${props.payload.impact}M</div>
                      <div className="text-xs text-slate-400">Retention: {props.payload.retention}%</div>
                    </div>,
                    ''
                  ];
                }
                return [value, name];
              }}
            />
            <Bar dataKey="subscribers" radius={[0, 8, 8, 0]}>
              {cohortData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.risk]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {cohortData.slice(0, 2).map((cohort) => (
          <div key={cohort.name} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-[#0064FF] transition-colors">
            <div className="text-xs text-slate-400 mb-2">{cohort.name}</div>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="font-bold text-2xl text-white">${cohort.impact}M</span>
              <span className="text-xs text-slate-500">Impact</span>
            </div>
            <div className="text-xs text-slate-400">
              Retention: <span className="text-red-400 font-medium">{cohort.retention}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
