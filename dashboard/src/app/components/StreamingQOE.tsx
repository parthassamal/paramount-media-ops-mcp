import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { Radio, PlayCircle, Gauge } from 'lucide-react';

const bufferingData = [
  { time: '00:00', value: 2.3, threshold: 2.5 },
  { time: '04:00', value: 1.8, threshold: 2.5 },
  { time: '08:00', value: 3.1, threshold: 2.5 },
  { time: '12:00', value: 4.2, threshold: 2.5 },
  { time: '16:00', value: 3.8, threshold: 2.5 },
  { time: '20:00', value: 5.6, threshold: 2.5 },
  { time: '23:59', value: 4.1, threshold: 2.5 }
];

const videoStartData = [
  { hour: '6AM', failures: 0.8 },
  { hour: '9AM', failures: 1.2 },
  { hour: '12PM', failures: 1.8 },
  { hour: '3PM', failures: 2.1 },
  { hour: '6PM', failures: 2.8 },
  { hour: '9PM', failures: 3.4 },
  { hour: '12AM', failures: 2.2 }
];

// EBVS (Experience-Based Video Score) - simulated gauge
const ebvsScore = 6.8; // out of 10

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-medium">{payload[0].payload.time || payload[0].payload.hour}</p>
        <p className="text-cyan-400 text-sm">{payload[0].value}%</p>
      </div>
    );
  }
  return null;
};

export function StreamingQOE() {
  // Calculate gauge rotation based on score (0-10 scale to -90 to 90 degrees)
  const gaugeRotation = ((ebvsScore / 10) * 180) - 90;

  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-cyan-500/10 p-2 rounded-lg">
            <Radio className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Streaming Quality of Experience (QoE)</h2>
            <p className="text-sm text-slate-400">Real-time performance metrics</p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Buffering Rate - Line Chart with Threshold Zones */}
        <div className="lg:col-span-2">
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-white mb-1">Buffering Ratio (24h)</h3>
            <p className="text-xs text-slate-500">Target: &lt;2.5% (green zone)</p>
          </div>
          <div className="h-56 bg-slate-900/50 rounded-lg p-3">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={bufferingData}>
                <defs>
                  <linearGradient id="bufferingGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="time" 
                  stroke="#94a3b8" 
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                />
                <YAxis 
                  stroke="#94a3b8" 
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  label={{ value: '%', angle: 0, position: 'insideTopLeft', fill: '#94a3b8' }}
                />
                {/* Threshold zones */}
                <ReferenceLine y={2.5} stroke="#10b981" strokeDasharray="3 3" label={{ value: 'Target', fill: '#10b981', fontSize: 10 }} />
                <ReferenceLine y={5} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Warning', fill: '#f59e0b', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#06b6d4" 
                  strokeWidth={2}
                  fill="url(#bufferingGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-slate-400">Good (&lt;2.5%)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-500 rounded"></div>
              <span className="text-slate-400">Warning (2.5-5%)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span className="text-slate-400">Critical (&gt;5%)</span>
            </div>
          </div>
        </div>

        {/* EBVS Gauge */}
        <div>
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-white mb-1">EBVS Score</h3>
            <p className="text-xs text-slate-500">Experience-Based Video Score</p>
          </div>
          <div className="h-56 bg-slate-900/50 rounded-lg p-4 flex flex-col items-center justify-center">
            {/* Gauge Visual */}
            <div className="relative w-40 h-40">
              {/* Background Arc */}
              <svg className="w-full h-full" viewBox="0 0 160 160">
                {/* Red Zone (0-33%) */}
                <path
                  d="M 20 80 A 60 60 0 0 1 50 26"
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                {/* Yellow Zone (33-66%) */}
                <path
                  d="M 50 26 A 60 60 0 0 1 110 26"
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                {/* Green Zone (66-100%) */}
                <path
                  d="M 110 26 A 60 60 0 0 1 140 80"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                {/* Needle */}
                <line
                  x1="80"
                  y1="80"
                  x2="80"
                  y2="30"
                  stroke="#0064FF"
                  strokeWidth="3"
                  strokeLinecap="round"
                  transform={`rotate(${gaugeRotation} 80 80)`}
                  className="transition-transform duration-700"
                />
                {/* Center Dot */}
                <circle cx="80" cy="80" r="6" fill="#0064FF" />
              </svg>
              
              {/* Score Display */}
              <div className="absolute inset-0 flex items-center justify-center pt-8">
                <div className="text-center">
                  <div className="text-4xl font-bold text-white">{ebvsScore}</div>
                  <div className="text-xs text-slate-400">out of 10</div>
                </div>
              </div>
            </div>

            {/* Score Interpretation */}
            <div className="mt-4 text-center">
              <div className={`inline-block px-3 py-1 rounded-full ${
                ebvsScore >= 8 ? 'bg-green-500/20 text-green-400' :
                ebvsScore >= 6 ? 'bg-amber-500/20 text-amber-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                <span className="text-sm font-medium">
                  {ebvsScore >= 8 ? 'Excellent' : ebvsScore >= 6 ? 'Fair' : 'Poor'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Video Start Failures - Bar Chart */}
      <div className="mt-6">
        <div className="mb-3">
          <h3 className="text-sm font-semibold text-white mb-1">Video Start Failures by Hour</h3>
          <p className="text-xs text-slate-500">Target: &lt;1.0% (below green line)</p>
        </div>
        <div className="h-48 bg-slate-900/50 rounded-lg p-3">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={videoStartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="hour" 
                stroke="#94a3b8" 
                tick={{ fill: '#94a3b8', fontSize: 11 }}
              />
              <YAxis 
                stroke="#94a3b8" 
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                label={{ value: '%', angle: 0, position: 'insideTopLeft', fill: '#94a3b8' }}
              />
              <ReferenceLine y={1.0} stroke="#10b981" strokeDasharray="3 3" label={{ value: 'Target', fill: '#10b981', fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="failures" 
                radius={[8, 8, 0, 0]}
                fill="#f43f5e"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-slate-800">
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Radio className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-slate-400">Avg Buffering</span>
            </div>
            <div className="font-bold text-xl text-cyan-400">3.6%</div>
            <div className="text-xs text-red-400 mt-1">↑ 45% vs target</div>
          </div>
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <PlayCircle className="w-4 h-4 text-rose-400" />
              <span className="text-xs text-slate-400">Start Failures</span>
            </div>
            <div className="font-bold text-xl text-rose-400">1.9%</div>
            <div className="text-xs text-red-400 mt-1">↑ 90% vs target</div>
          </div>
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Gauge className="w-4 h-4 text-amber-400" />
              <span className="text-xs text-slate-400">EBVS Score</span>
            </div>
            <div className="font-bold text-xl text-amber-400">{ebvsScore}/10</div>
            <div className="text-xs text-amber-400 mt-1">Fair quality</div>
          </div>
        </div>
      </div>
    </div>
  );
}