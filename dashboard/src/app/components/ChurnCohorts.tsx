import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Users } from 'lucide-react';

const cohortData = [
  {
    name: 'High-Value Serial Churners',
    subscribers: 850000,
    impact: 425,
    risk: 'critical'
  },
  {
    name: 'Price-Sensitive Millennials',
    subscribers: 720000,
    impact: 288,
    risk: 'high'
  },
  {
    name: 'Content-Starved Families',
    subscribers: 540000,
    impact: 162,
    risk: 'high'
  },
  {
    name: 'Platform Migration Risk',
    subscribers: 380000,
    impact: 90,
    risk: 'medium'
  }
];

const COLORS = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#eab308'
};

export function ChurnCohorts() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/10 p-2 rounded-lg">
            <Users className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h2 className="font-bold text-white">Top Churn Risk Cohorts</h2>
            <p className="text-sm text-slate-400">Subscriber segments by churn probability</p>
          </div>
        </div>
      </div>

      <div className="h-80 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={cohortData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              type="number" 
              stroke="#94a3b8" 
              tick={{ fill: '#94a3b8' }}
              label={{ value: 'Subscribers (thousands)', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
              tickFormatter={(value) => `${value / 1000}K`}
            />
            <YAxis 
              type="category" 
              dataKey="name" 
              stroke="#94a3b8" 
              tick={{ fill: '#94a3b8' }}
              width={180}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9'
              }}
              formatter={(value: number, name: string) => {
                if (name === 'subscribers') return [value.toLocaleString(), 'Subscribers'];
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

      <div className="mt-4 grid grid-cols-2 gap-3">
        {cohortData.slice(0, 2).map((cohort) => (
          <div key={cohort.name} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="text-xs text-slate-400 mb-1">{cohort.name}</div>
            <div className="font-bold text-white">${cohort.impact}M Impact</div>
          </div>
        ))}
      </div>
    </div>
  );
}