import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Radio, PlayCircle } from 'lucide-react';

const streamingData = [
  { time: '00:00', bufferingRatio: 2.3, videoStartFailures: 1.2 },
  { time: '04:00', bufferingRatio: 1.8, videoStartFailures: 0.9 },
  { time: '08:00', bufferingRatio: 3.1, videoStartFailures: 1.8 },
  { time: '12:00', bufferingRatio: 4.2, videoStartFailures: 2.4 },
  { time: '16:00', bufferingRatio: 3.8, videoStartFailures: 2.1 },
  { time: '20:00', bufferingRatio: 5.6, videoStartFailures: 3.2 },
  { time: '23:59', bufferingRatio: 4.1, videoStartFailures: 2.3 }
];

export function StreamingMetrics() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-cyan-500/10 p-2 rounded-lg">
            <Radio className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="font-bold text-white">Streaming Quality Metrics</h2>
            <p className="text-sm text-slate-400">24-hour performance tracking</p>
          </div>
        </div>
      </div>

      <div className="h-80 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={streamingData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey="time" 
              stroke="#94a3b8" 
              tick={{ fill: '#94a3b8' }}
            />
            <YAxis 
              stroke="#94a3b8" 
              tick={{ fill: '#94a3b8' }}
              label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9'
              }}
              formatter={(value: number) => `${value}%`}
            />
            <Legend 
              wrapperStyle={{ color: '#94a3b8' }}
            />
            <Line 
              type="monotone" 
              dataKey="bufferingRatio" 
              stroke="#06b6d4" 
              strokeWidth={2}
              dot={{ fill: '#06b6d4', r: 4 }}
              name="Buffering Ratio"
            />
            <Line 
              type="monotone" 
              dataKey="videoStartFailures" 
              stroke="#f43f5e" 
              strokeWidth={2}
              dot={{ fill: '#f43f5e', r: 4 }}
              name="Video Start Failures"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-slate-400">Avg Buffering Ratio</span>
          </div>
          <div className="font-bold text-xl text-cyan-400">3.6%</div>
          <div className="text-xs text-slate-500 mt-1">Target: &lt;2.5%</div>
        </div>
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <PlayCircle className="w-4 h-4 text-rose-400" />
            <span className="text-sm text-slate-400">Video Start Failures</span>
          </div>
          <div className="font-bold text-xl text-rose-400">1.9%</div>
          <div className="text-xs text-slate-500 mt-1">Target: &lt;1.0%</div>
        </div>
      </div>
    </div>
  );
}