import React, { useState, useEffect } from 'react';
import { MetricsGrid } from './components/MetricsGrid';
import { ChurnCohorts } from './components/ChurnCohorts';
import { StreamingMetrics } from './components/StreamingMetrics';
import { ProductionTracking } from './components/ProductionTracking';
import { ParetoChart } from './components/ParetoChart';
import { ParamountLogo } from './components/ParamountLogo';
import { TrendingUp, Activity, Sparkles, RefreshCw } from 'lucide-react';

export default function App() {
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setLastUpdated(new Date());
    // Trigger refresh of data (would call API in real implementation)
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--paramount-bg-primary)' }}>
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-30">
        <div className="absolute w-96 h-96 bg-[var(--paramount-blue)] rounded-full blur-3xl -top-48 -left-48 animate-pulse"></div>
        <div className="absolute w-96 h-96 bg-[var(--paramount-orange)] rounded-full blur-3xl -bottom-48 -right-48 animate-pulse delay-1000"></div>
      </div>

      {/* Header */}
      <header className="paramount-glass border-b sticky top-0 z-50" style={{ borderColor: 'var(--paramount-border)' }}>
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Title */}
            <div className="flex items-center gap-4">
              <ParamountLogo className="w-52 h-14 text-white" />
              <div className="h-10 w-px bg-[var(--paramount-border)]"></div>
              <div className="paramount-live-indicator">
                <span className="paramount-live-dot"></span>
                <span>LIVE</span>
              </div>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center gap-4">
              {/* Last Updated */}
              <div className="text-sm" style={{ color: 'var(--paramount-text-muted)' }}>
                <span>Updated: {lastUpdated.toLocaleTimeString()}</span>
              </div>

              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="paramount-btn-primary flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>

              {/* Annual Impact Card */}
              <div 
                className="flex items-center gap-3 px-4 py-2 rounded-lg border"
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderColor: 'rgba(239, 68, 68, 0.3)'
                }}
              >
                <TrendingUp className="w-5 h-5" style={{ color: 'var(--paramount-danger)' }} />
                <div className="text-sm">
                  <span style={{ color: 'var(--paramount-text-muted)' }}>Revenue at Risk:</span>
                  <span className="ml-2 font-bold" style={{ color: 'var(--paramount-danger)' }}>$2.1M</span>
                </div>
              </div>
            </div>
          </div>

          {/* AI Insights Banner */}
          <div 
            className="mt-4 p-4 rounded-lg border"
            style={{
              background: 'rgba(0, 100, 255, 0.1)',
              borderColor: 'rgba(0, 100, 255, 0.3)'
            }}
          >
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 mt-0.5" style={{ color: 'var(--paramount-blue)' }} />
              <div>
                <h3 className="font-semibold mb-1" style={{ color: 'var(--paramount-blue-light)' }}>
                  🤖 AI-Powered Insight
                </h3>
                <p className="text-sm" style={{ color: 'var(--paramount-text-secondary)' }}>
                  <strong>80% of churn</strong> comes from <strong>20% of content genres</strong> → 
                  Focus retention campaigns on Reality TV (42% churn risk, 125K subscribers at risk). 
                  Projected ROI: <span className="font-bold text-[var(--paramount-success)]">$450K saved</span>.
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-[1800px] mx-auto px-6 py-8 space-y-8">
        {/* Top Metrics */}
        <MetricsGrid />

        {/* Charts Row */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <ChurnCohorts />
          <ParetoChart />
        </div>

        {/* Streaming & Production Row */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <StreamingMetrics />
          <ProductionTracking />
        </div>

        {/* Footer */}
        <div className="text-center pt-8 pb-4" style={{ color: 'var(--paramount-text-muted)' }}>
          <p className="text-sm">
            Powered by <span className="paramount-gradient-text font-semibold">AI + MCP Protocol</span> | 
            Integrations: JIRA • Confluence • Conviva • NewRelic • Analytics
          </p>
        </div>
      </main>
    </div>
  );
}
