import { useState, useEffect, useCallback } from "react";
import { AIInsightsPanel } from "./components/AIInsightsPanel";
import { ExecutiveKPIs } from "./components/ExecutiveKPIs";
import { ProductionIssuesTable } from "./components/ProductionIssuesTable";
import { StreamingQOE } from "./components/StreamingQOE";
import { ChurnCohorts } from "./components/ChurnCohorts";
import { ParetoChart } from "./components/ParetoChart";
import { HumanReviewQueue } from "./components/HumanReviewQueue";
import { Sidebar } from "./components/Sidebar";
import { LoginScreen } from "./components/LoginScreen";
import { HelpModal } from "./components/HelpModal";
import { PipelineStatusPage, RcaArtifactsPage } from "./components/phase1";
import { IntegrationsPage } from "./components/system";
import { MissionControlPage } from "./components/mission/MissionControlPage";
import { IncidentDetailPage } from "./components/mission/IncidentDetailPage";
import { GovernancePanel } from "./components/mission/GovernancePanel";
import {
  TestImpactPage,
  FailureTriagePage,
  SuiteHygienePage,
  DeploymentRiskPage,
  PatternDetectionPage,
  AlertTestsPage,
  EffectivenessPage,
} from "./components/phase2";
import { Moon, Sun, Download, Wifi, Palette, RefreshCw } from "lucide-react";
import ErrorBoundary from "../utils/ErrorBoundary";
import { API_BASE } from "../config/api";

interface User {
  name: string;
  email: string;
}

function AppContent() {
  const [darkMode, setDarkMode] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isFigmaLive, setIsFigmaLive] = useState(false);
  const [figmaHeroImage, setFigmaHeroImage] = useState<string | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState("mission-control");
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem("paramount_user");
    return saved ? JSON.parse(saved) : null;
  });

  // Live counts for sidebar badges
  const [counts, setCounts] = useState({
    totalIssues: 0,
    criticalInsights: 0,
    pendingReview: 0,
    hygieneFlags: 0,
    patternsDetected: 0,
    governancePending: 0,
  });

  // Fetch counts for badges
  const fetchCounts = useCallback(async () => {
    try {
      const [issuesRes, reviewRes, govRes] = await Promise.all([
        fetch(`${API_BASE}/api/jira/issues`),
        fetch(`${API_BASE}/api/rca/review/pending`),
        fetch(`${API_BASE}/api/governance/stats`).catch(() => null),
      ]);

      if (issuesRes.ok) {
        const issues = await issuesRes.json();
        const critical = issues.filter(
          (i: any) => i.severity === "critical" || /\bP1\b/i.test(i.summary)
        ).length;
        setCounts((prev) => ({
          ...prev,
          totalIssues: issues.length,
          criticalInsights: critical,
        }));
      }

      if (reviewRes.ok) {
        const reviews = await reviewRes.json();
        setCounts((prev) => ({
          ...prev,
          pendingReview: reviews.pending?.length || 0,
        }));
      }

      if (govRes && govRes.ok) {
        const govStats = await govRes.json();
        setCounts((prev) => ({
          ...prev,
          governancePending: govStats.awaiting_review || 0,
        }));
      }
    } catch (error) {
      console.warn("Failed to fetch counts:", error);
    }
  }, []);

  // Live Figma Sync
  useEffect(() => {
    const fetchFigmaAssets = async () => {
      try {
        const cssResponse = await fetch(`${API_BASE}/figma/css-variables`);
        if (cssResponse.ok) {
          const { css } = await cssResponse.json();
          let styleTag = document.getElementById("figma-live-styles");
          if (!styleTag) {
            styleTag = document.createElement("style");
            styleTag.id = "figma-live-styles";
            document.head.appendChild(styleTag);
          }
          styleTag.textContent = css;
          setIsFigmaLive(true);
        }

        const imgResponse = await fetch(`${API_BASE}/figma/images`);
        if (imgResponse.ok) {
          const { images } = await imgResponse.json();
          const heroUrl = Object.values(images)[0] as string;
          if (heroUrl && !heroUrl.includes("sample-image")) {
            setFigmaHeroImage(heroUrl);
          }
        }
      } catch (error) {
        console.warn("Figma assets sync unavailable:", error);
      }
    };

    fetchFigmaAssets();
  }, []);

  // Periodic updates
  useEffect(() => {
    fetchCounts();
    const interval = setInterval(() => {
      setLastUpdated(new Date());
      fetchCounts();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchCounts]);

  // Persist user to localStorage
  useEffect(() => {
    if (user) {
      localStorage.setItem("paramount_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("paramount_user");
    }
  }, [user]);

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
    setCurrentPage("login");
  };

  const handleNavigate = (page: string) => {
    if (page === "help") {
      setHelpOpen(true);
    } else {
      setCurrentPage(page);
    }
  };

  const handleExportPDF = async () => {
    try {
      const [healthRes, issuesRes, missionRes, govRes, reviewRes] = await Promise.all([
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/api/jira/issues`),
        fetch(`${API_BASE}/api/mission-control/summary`).catch(() => null),
        fetch(`${API_BASE}/api/governance/stats`).catch(() => null),
        fetch(`${API_BASE}/api/rca/review/pending`).catch(() => null),
      ]);

      const health = healthRes.ok ? await healthRes.json() : {};
      const issues = issuesRes.ok ? await issuesRes.json() : [];
      const mission = missionRes?.ok ? await missionRes.json() : null;
      const govStats = govRes?.ok ? await govRes.json() : null;
      const reviewData = reviewRes?.ok ? await reviewRes.json() : null;

      const liveIntegrations = health.integrations
        ? Object.values(health.integrations).filter((i: any) => i?.status === "live").length
        : 0;
      const totalIssues = issues.length;
      const criticalIssues = issues.filter(
        (i: any) => i.severity === "critical" || /\bP1\b/i.test(i.summary)
      ).length;
      const highIssues = issues.filter(
        (i: any) => i.severity === "high" || /\bP2\b/i.test(i.summary)
      ).length;
      const totalCost = issues.reduce((s: number, i: any) => s + (i.cost_impact ?? 0), 0);

      const topIncident = mission?.top_incident;
      const pendingReviews = reviewData?.count ?? 0;
      const pendingApprovals = govStats?.awaiting_review ?? 0;

      const dashboardSnapshot = {
        metrics: {
          "Total Production Issues": String(totalIssues),
          "Critical Issues": String(criticalIssues),
          "High Priority Issues": String(highIssues),
          "Live Integrations": String(liveIntegrations),
          "Revenue at Risk": totalCost > 0 ? `$${totalCost.toLocaleString()}` : `$${(criticalIssues * 500000 + highIssues * 200000).toLocaleString()}`,
          "Pending RCA Reviews": String(pendingReviews),
          "Pending Governance Approvals": String(pendingApprovals),
          "System Mode": mission?.system_mode ?? "unknown",
        },
        insights: issues.slice(0, 8).map((i: any) => `[${i.id || i.key}] ${i.summary} — ${i.severity} — $${(i.cost_impact ?? 0).toLocaleString()} (${i.status})`),
        top_incident: topIncident ? {
          id: topIncident.incident_id,
          summary: topIncident.summary,
          priority_score: topIncident.priority_score,
          top_action: topIncident.top_action,
        } : null,
        governance: {
          total_reviews: govStats?.total ?? 0,
          awaiting_review: pendingApprovals,
          approved: govStats?.approved ?? 0,
          rejected: govStats?.rejected ?? 0,
        },
        recommendations: [
          criticalIssues > 0
            ? `Immediate attention needed for ${criticalIssues} critical issue(s)`
            : "No critical issues - maintain current monitoring",
          `${liveIntegrations} integrations connected and reporting live data`,
          pendingReviews > 0 ? `${pendingReviews} RCA review(s) pending human approval (24h SLA)` : "All RCA reviews processed",
          pendingApprovals > 0 ? `${pendingApprovals} governance approval(s) awaiting action` : "No pending governance approvals",
          topIncident ? `Top priority: ${topIncident.incident_id} — recommended action: ${topIncident.top_action || "review"}` : "No active high-priority incidents",
        ],
        timestamp: new Date().toISOString(),
        figma_sync: isFigmaLive,
        figma_image_url: figmaHeroImage || null,
      };

      const response = await fetch(`${API_BASE}/adobe/export-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: "executive",
          data: dashboardSnapshot,
          upload_to_cloud: false,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        window.location.href = `${API_BASE}/adobe/download-report/${result.filename}`;
      } else {
        const error = await response.json();
        alert(`Export Failed: ${error.detail || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Export error:", error);
      alert("Connection error to PDF service");
    }
  };

  // Show login screen if not authenticated
  if (!user || currentPage === "login") {
    return <LoginScreen onLogin={handleLogin} onNavigate={handleNavigate} />;
  }

  // Render page content based on current page
  const renderPageContent = () => {
    switch (currentPage) {
      case "mission-control":
        return (
          <MissionControlPage
            onNavigateToIncident={(id: string) => {
              setSelectedIncidentId(id);
              setCurrentPage("incident-detail");
            }}
          />
        );

      case "incident-detail":
        return selectedIncidentId ? (
          <IncidentDetailPage
            incidentId={selectedIncidentId}
            onBack={() => setCurrentPage("mission-control")}
          />
        ) : (
          <MissionControlPage
            onNavigateToIncident={(id: string) => {
              setSelectedIncidentId(id);
              setCurrentPage("incident-detail");
            }}
          />
        );

      case "governance":
        return (
          <div className="max-w-4xl">
            <GovernancePanel />
          </div>
        );

      case "dashboard":
        return (
          <div className="space-y-6">
            <ExecutiveKPIs />
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2">
                <AIInsightsPanel />
              </div>
              <div className="xl:col-span-1 space-y-6">
                <HumanReviewQueue />
                <ParetoChart />
              </div>
            </div>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <StreamingQOE />
              <ChurnCohorts />
            </div>
          </div>
        );

      case "ai-insights":
        return <AIInsightsPanel fullPage />;

      case "production-issues":
        return <ProductionIssuesTable />;

      case "review-queue":
        return (
          <div className="max-w-4xl">
            <HumanReviewQueue fullPage />
          </div>
        );

      case "pipeline-status":
        return <PipelineStatusPage />;

      case "rca-artifacts":
        return <RcaArtifactsPage />;

      case "test-impact":
        return <TestImpactPage />;

      case "failure-triage":
        return <FailureTriagePage />;

      case "suite-hygiene":
        return <SuiteHygienePage />;

      case "deployment-risk":
        return <DeploymentRiskPage />;

      case "pattern-detection":
        return <PatternDetectionPage />;

      case "alert-tests":
        return <AlertTestsPage />;

      case "effectiveness":
        return <EffectivenessPage />;

      case "integrations":
        return <IntegrationsPage />;

      default:
        return (
          <div className="space-y-6">
            <ExecutiveKPIs />
            <ProductionIssuesTable />
          </div>
        );
    }
  };

  const getPageTitle = () => {
    const titles: Record<string, string> = {
      "mission-control": "Mission Control",
      "incident-detail": "Incident Detail",
      governance: "Governance & Approvals",
      dashboard: "Dashboard",
      "ai-insights": "AI Insights",
      "production-issues": "Production Issues",
      "review-queue": "Human Review Queue",
      "pipeline-status": "Pipeline Status",
      "rca-artifacts": "RCA Artifacts",
      "test-impact": "Test Impact Analysis",
      "failure-triage": "Automated Failure Triage",
      "suite-hygiene": "Suite Hygiene",
      "deployment-risk": "Deployment Risk Score",
      "pattern-detection": "Pattern Detection",
      "alert-tests": "Alert-Driven Tests",
      effectiveness: "Test Effectiveness",
      integrations: "Integrations",
    };
    return titles[currentPage] || "Mission Control";
  };

  return (
    <div className={darkMode ? "dark min-h-screen" : "min-h-screen"}>
      <div className="min-h-screen bg-background text-foreground flex">
        {/* Sidebar */}
        <Sidebar
          currentPage={currentPage}
          onNavigate={handleNavigate}
          onLogout={handleLogout}
          user={user}
          counts={counts}
        />

        {/* Main Content Area */}
        <div className="flex-1 ml-64">
          {/* Header */}
          <header className="border-b border-border bg-card backdrop-blur-sm sticky top-0 z-30 shadow-lg">
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <h1 className="text-xl font-bold text-foreground">{getPageTitle()}</h1>
                  {isFigmaLive && (
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-[10px] text-blue-400 uppercase tracking-widest">
                      <Palette size={10} />
                      Figma Live
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4">
                  {/* Live Indicator */}
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <div className="relative">
                      <Wifi className="w-4 h-4 text-green-400" />
                      <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    </div>
                    <span className="text-xs font-medium text-green-400">Live</span>
                  </div>

                  {/* Last Updated */}
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <RefreshCw className="w-3 h-3" />
                    {lastUpdated.toLocaleTimeString()}
                  </div>

                  {/* Export PDF */}
                  <button
                    onClick={handleExportPDF}
                    className="flex items-center gap-2 px-4 py-2 bg-[#0064FF] hover:bg-[#0052CC] rounded-lg transition-all text-sm font-medium"
                  >
                    <Download className="w-4 h-4" />
                    Export PDF
                  </button>

                  {/* Dark Mode Toggle */}
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    className="p-2 rounded-lg bg-muted hover:bg-accent transition-all"
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

          {/* Page Content */}
          <main className="p-6">{renderPageContent()}</main>

          {/* Footer */}
          <footer className="border-t border-border py-4 px-6">
            <div className="text-center text-xs text-muted-foreground">
              Paramount+ AI Operations Dashboard &bull; Built for AI Hackathon &bull; Real-time monitoring &amp;
              predictive analytics
            </div>
          </footer>
        </div>

        {/* Help Modal */}
        <HelpModal open={helpOpen} onClose={() => setHelpOpen(false)} />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
