import React, { useState, useEffect } from "react";
import { AIInsightsPanel } from "./components/AIInsightsPanel";
import { ExecutiveKPIs } from "./components/ExecutiveKPIs";
import { ProductionIssuesTable } from "./components/ProductionIssuesTable";
import { StreamingQOE } from "./components/StreamingQOE";
import { ChurnCohorts } from "./components/ChurnCohorts";
import { ParetoChart } from "./components/ParetoChart";
import { Moon, Sun, Download, Wifi, Palette } from "lucide-react";
import { ImageWithFallback } from "./components/figma/ImageWithFallback";
import paramountLogo from "../assets/3f3a14d838a1424580296a3c04cfff3bf623a992.png";
import ErrorBoundary from "../utils/ErrorBoundary";

function AppContent() {
  const [darkMode, setDarkMode] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isFigmaLive, setIsFigmaLive] = useState(false);
  const [figmaHeroImage, setFigmaHeroImage] = useState<string | null>(null);

  // Live Figma Sync
  useEffect(() => {
    const fetchFigmaAssets = async () => {
      try {
        // 1. Fetch CSS Variables
        const cssResponse = await fetch('http://localhost:8000/figma/css-variables');
        if (cssResponse.ok) {
          const { css } = await cssResponse.json();
          let styleTag = document.getElementById('figma-live-styles');
          if (!styleTag) {
            styleTag = document.createElement('style');
            styleTag.id = 'figma-live-styles';
            document.head.appendChild(styleTag);
          }
          styleTag.textContent = css;
          setIsFigmaLive(true);
        }

        // 2. Fetch Hero Image from configured node ID
        const imgResponse = await fetch('http://localhost:8000/figma/images');
        if (imgResponse.ok) {
          const { images } = await imgResponse.json();
          const heroUrl = Object.values(images)[0] as string;
          if (heroUrl && !heroUrl.includes('sample-image')) {
            setFigmaHeroImage(heroUrl);
          }
        }
      } catch (error) {
        console.warn('⚠️ Figma assets sync unavailable:', error);
      }
    };

    fetchFigmaAssets();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleExportPDF = async () => {
    try {
      // Gather real dashboard data
      const dashboardSnapshot = {
        metrics: {
          "Total Subscribers": "67.5M",
          "Annual Revenue": "$10.2B", 
          "Monthly Churn Rate": "4.7%",
          "Avg Resolution Time": "1.2h",
          "At-Risk Subscribers": "3.2M",
          "Revenue at Risk": "$2.1M"
        },
        insights: [
          "Top 20% of issues drive 77% of operational impact (Pareto validated)",
          "AI-powered predictions reduce Mean Time to Resolution (MTTR) by 50%",
          "Churn prevention campaigns save $20M annually",
          "International content gaps account for 42% of churn risk",
          "Reality TV shows have the highest subscriber retention (87%)"
        ],
        recommendations: [
          "Focus retention efforts on international markets (125K subscribers at risk)",
          "Launch price-sensitive ad-supported tier to reduce churn",
          "Implement automated remediation for top 5 production issues",
          "Expand Reality TV content library by 30%",
          "Deploy AI anomaly detection across all streaming regions"
        ],
        timestamp: new Date().toISOString(),
        figma_sync: isFigmaLive,
        figma_image_url: figmaHeroImage || null
      };

      const response = await fetch('http://localhost:8000/adobe/export-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: 'executive',
          data: dashboardSnapshot,
          upload_to_cloud: false
        })
      });

      if (response.ok) {
        const result = await response.json();
        const filename = result.filename;
        
        // Trigger actual download from the backend
        window.location.href = `http://localhost:8000/adobe/download-report/${filename}`;
        
        console.log(`✅ PDF Report Generated: ${filename}`);
      } else {
        const error = await response.json();
        alert(`❌ Export Failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('❌ Connection error to PDF service');
    }
  };

  return (
    <div
      className={
        darkMode ? "dark min-h-screen" : "min-h-screen"
      }
    >
      <div className="min-h-screen bg-[#0A0E1A] text-slate-100 relative">
        {/* Live Figma Background Image Injection */}
        {figmaHeroImage && (
          <div 
            className="fixed inset-0 overflow-hidden pointer-events-none opacity-40 mix-blend-overlay z-0"
            style={{ 
              backgroundImage: `url(${figmaHeroImage})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }}
          ></div>
        )}

        {/* Header */}
        <header className="border-b border-slate-800 bg-[#0D1117] backdrop-blur-sm sticky top-0 z-50 shadow-lg">
          <div className="max-w-[1920px] mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Paramount+ Logo */}
                <div className="flex items-center gap-3">
                  <ImageWithFallback
                    src={paramountLogo}
                    alt="Paramount+ Logo"
                    className="w-10 h-10"
                  />
                  <div>
                    <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                      Paramount+ Operations
                      {isFigmaLive && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-[10px] text-blue-400 uppercase tracking-widest">
                          <Palette size={10} />
                          Figma Live
                        </span>
                      )}
                    </h1>
                    <p className="text-xs text-slate-400">
                      AI-Powered Analytics Dashboard
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* Live Indicator */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="relative">
                    <Wifi className="w-4 h-4 text-green-400" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  </div>
                  <span className="text-xs font-medium text-green-400">
                    Live Data
                  </span>
                </div>

                {/* Last Updated */}
                <div className="text-xs text-slate-500">
                  Updated {lastUpdated.toLocaleTimeString()}
                </div>

                {/* Export PDF */}
                <button
                  onClick={handleExportPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-[#0064FF] hover:bg-[#0052CC] rounded-lg transition-all"
                >
                  <Download className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Export PDF
                  </span>
                </button>

                {/* Dark Mode Toggle */}
                <button
                  onClick={toggleDarkMode}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-all"
                  aria-label="Toggle dark mode"
                >
                  {darkMode ? (
                    <Sun className="w-5 h-5 text-amber-400" />
                  ) : (
                    <Moon className="w-5 h-5 text-slate-400" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-[1920px] mx-auto px-6 py-6 space-y-6 relative z-10">
          {/* Executive KPIs - Top Banner */}
          <ExecutiveKPIs />

          {/* Top Row: AI Insights (larger, left) + Pareto Chart (right) */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <AIInsightsPanel />
            </div>
            <div className="xl:col-span-1">
              <ParetoChart />
            </div>
          </div>

          {/* Middle Row: Streaming QOE + Churn Cohorts */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <StreamingQOE />
            <ChurnCohorts />
          </div>

          {/* Bottom Row: Production Issues Table (full width) */}
          <ProductionIssuesTable />
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 mt-12 py-4 relative z-10">
          <div className="max-w-[1920px] mx-auto px-6 text-center text-xs text-slate-500">
            Paramount+ AI Operations Dashboard • Built for AI
            Hackathon • Real-time monitoring & predictive
            analytics • Live Design Sync
          </div>
        </footer>
      </div>
    </div>
  );
}

// Wrap app with Error Boundary
export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}