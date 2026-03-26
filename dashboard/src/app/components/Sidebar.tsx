import React, { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Brain,
  AlertTriangle,
  ClipboardCheck,
  GitBranch,
  FileText,
  Target,
  Filter,
  Sparkles,
  TrendingUp,
  Bell,
  Zap,
  BarChart3,
  Settings,
  HelpCircle,
  LogOut,
  ChevronDown,
  ChevronRight,
  Activity,
  Shield,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  badge?: number | string;
  badgeColor?: string;
  children?: NavItem[];
}

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  onLogout: () => void;
  user: { name: string; email: string; avatar?: string } | null;
  counts: {
    totalIssues: number;
    criticalInsights: number;
    pendingReview: number;
    hygieneFlags: number;
    patternsDetected: number;
    governancePending?: number;
  };
}

const navSections: { title: string; items: NavItem[] }[] = [
  {
    title: "Overview",
    items: [
      { id: "mission-control", label: "Mission Control", icon: Shield },
      { id: "dashboard", label: "Operations Overview", icon: LayoutDashboard },
      { id: "ai-insights", label: "AI Insights", icon: Brain },
    ],
  },
  {
    title: "Phase 1 — RCA Pipeline",
    items: [
      { id: "production-issues", label: "Production Issues", icon: AlertTriangle },
      { id: "review-queue", label: "Review Queue", icon: ClipboardCheck },
      { id: "governance", label: "Governance", icon: Shield },
      { id: "pipeline-status", label: "Pipeline Status", icon: GitBranch },
      { id: "rca-artifacts", label: "RCA Artifacts", icon: FileText },
    ],
  },
  {
    title: "Phase 2 — QA Intelligence",
    items: [
      { id: "test-impact", label: "Test Impact Analysis", icon: Target },
      { id: "failure-triage", label: "Failure Triage", icon: Filter },
      { id: "suite-hygiene", label: "Suite Hygiene", icon: Sparkles },
      { id: "deployment-risk", label: "Deployment Risk", icon: TrendingUp },
      { id: "pattern-detection", label: "Pattern Detection", icon: Activity },
      { id: "alert-tests", label: "Alert-Driven Tests", icon: Bell },
      { id: "effectiveness", label: "Test Effectiveness", icon: Zap },
    ],
  },
  {
    title: "System",
    items: [
      { id: "integrations", label: "Integrations", icon: Settings },
      { id: "help", label: "Help & Docs", icon: HelpCircle },
    ],
  },
];

export function Sidebar({ currentPage, onNavigate, onLogout, user, counts }: SidebarProps) {
  const [expandedSections, setExpandedSections] = useState<string[]>([
    "Overview",
    "Phase 1 — RCA Pipeline",
  ]);

  const toggleSection = (title: string) => {
    setExpandedSections((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]
    );
  };

  const getBadge = (itemId: string): { count?: number | string; color: string } | null => {
    switch (itemId) {
      case "production-issues":
        return counts.totalIssues > 0
          ? { count: counts.totalIssues, color: "bg-slate-600" }
          : null;
      case "mission-control":
        return counts.criticalInsights > 0
          ? { count: counts.criticalInsights, color: "bg-red-500" }
          : null;
      case "ai-insights":
        return counts.criticalInsights > 0
          ? { count: counts.criticalInsights, color: "bg-red-500" }
          : null;
      case "review-queue":
        return counts.pendingReview > 0
          ? { count: counts.pendingReview, color: "bg-amber-500" }
          : null;
      case "suite-hygiene":
        return counts.hygieneFlags > 0
          ? { count: counts.hygieneFlags, color: "bg-orange-500" }
          : null;
      case "pattern-detection":
        return counts.patternsDetected > 0
          ? { count: counts.patternsDetected, color: "bg-purple-500" }
          : null;
      case "governance":
        return (counts.governancePending ?? 0) > 0
          ? { count: counts.governancePending!, color: "bg-amber-500" }
          : null;
      default:
        return null;
    }
  };

  return (
    <aside className="w-64 h-screen bg-card border-r border-border flex flex-col fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0064FF] to-purple-600 flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-foreground">Paramount+</h1>
            <p className="text-xs text-muted-foreground">AI Operations</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 pb-8">
        {navSections.map((section) => (
          <div key={section.title} className="mb-4">
            <button
              onClick={() => toggleSection(section.title)}
              className="flex items-center justify-between w-full px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:text-foreground transition-colors"
            >
              <span>{section.title}</span>
              {expandedSections.includes(section.title) ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
            </button>

            {expandedSections.includes(section.title) && (
              <div className="mt-1 space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const badge = getBadge(item.id);
                  const isActive = currentPage === item.id;

                  return (
                    <button
                      key={item.id}
                      onClick={() => onNavigate(item.id)}
                      className={`
                        flex items-center justify-between w-full px-3 py-2 rounded-lg text-sm
                        transition-all duration-150
                        ${
                          isActive
                            ? "bg-primary/20 text-primary font-medium"
                            : "text-muted-foreground hover:bg-accent hover:text-foreground"
                        }
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="w-4 h-4" />
                        <span>{item.label}</span>
                      </div>
                      {badge && (
                        <span
                          className={`
                            px-1.5 py-0.5 text-xs font-medium rounded-full text-white
                            ${badge.color}
                          `}
                        >
                          {badge.count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* User Profile & Logout */}
      <div className="shrink-0 p-3 border-t border-border">
        {user ? (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-semibold text-xs shrink-0">
              {user.name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{user.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user.email}</p>
            </div>
            <button
              onClick={onLogout}
              className="shrink-0 p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => onNavigate("login")}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign in</span>
          </button>
        )}
      </div>
    </aside>
  );
}
