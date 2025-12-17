import React from 'react';
import { MetricsGrid } from './components/MetricsGrid';
import { ChurnCohorts } from './components/ChurnCohorts';
import { StreamingMetrics } from './components/StreamingMetrics';
import { ProductionTracking } from './components/ProductionTracking';
import { ParetoChart } from './components/ParetoChart';
import { TrendingUp, Activity } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Paramount+ Operations Dashboard</h1>
                <p className="text-sm text-slate-400">Real-time analytics & performance monitoring</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-red-400" />
              <div className="text-sm">
                <span className="text-slate-400">Annual Churn Impact:</span>
                <span className="ml-2 font-bold text-red-400">$965M</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
        {/* Top Metrics */}
        <MetricsGrid />

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChurnCohorts />
          <ParetoChart />
        </div>

        {/* Streaming & Production Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <StreamingMetrics />
          <ProductionTracking />
        </div>
      </main>
    </div>
  );
}
