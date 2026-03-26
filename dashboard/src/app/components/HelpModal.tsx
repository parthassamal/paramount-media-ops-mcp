import React from "react";
import {
  X,
  Database,
  Brain,
  BarChart3,
  Shield,
  Layers,
  ArrowRight,
  Zap,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  Radio,
  Users,
  FileText,
} from "lucide-react";

interface HelpModalProps {
  open: boolean;
  onClose: () => void;
}

const sections = [
  {
    id: "overview",
    icon: Zap,
    title: "What is this app?",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    content: `Paramount+ Media Ops is an incident intelligence and RCA actioning control plane. The core promise is: detect the highest-impact incident, explain it with normalized evidence, recommend the next action with confidence and business impact, route approval when needed, generate verification tests, and track measurable recovery.`,
  },
  {
    id: "operator-loop",
    icon: Users,
    title: "Operator workflow (Mission Control)",
    color: "text-sky-400",
    bg: "bg-sky-500/10",
    border: "border-sky-500/30",
    content: null,
    list: [
      {
        label: "1) Detect",
        desc: "Mission Control ranks open incidents using deterministic decision scoring (operational severity, subscriber impact, business risk, confidence).",
      },
      {
        label: "2) Explain",
        desc: "Evidence is normalized into a single bundle and rendered with timeline events, source references, and blast radius context.",
      },
      {
        label: "3) Recommend",
        desc: "Every action proposal includes confidence, rationale, expected impact, owner, and validation plan.",
      },
      {
        label: "4) Approve",
        desc: "High-risk actions require review. Governance state and SLA are visible in the UI and persisted in audit logs.",
      },
      {
        label: "5) Verify",
        desc: "Approved actions generate or run targeted verification tests with TestRail writeback and post-fix status checks.",
      },
      {
        label: "6) Measure",
        desc: "Cycle-time, review latency, and action outcomes are tracked so teams can prove recovery and improve runbooks.",
      },
    ],
  },
  {
    id: "data-sources",
    icon: Database,
    title: "How is data sourced?",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    content: null,
    list: [
      {
        label: "Jira (Atlassian Cloud)",
        desc: "Production issues are fetched in real-time from your Jira project via REST API. Each issue's key, summary, severity, status, assignee, team (computed from components), cost impact, and delay days are displayed across the dashboard. The API is polled every 30 seconds with a TTL cache to prevent redundant calls.",
      },
      {
        label: "New Relic (NerdGraph GraphQL)",
        desc: "Application performance metrics (response time, error rate, throughput, Apdex), infrastructure health, and alert incidents are queried via New Relic's NerdGraph API. The Streaming QoE section uses this data to derive the EBVS score and buffering metrics. Includes exponential backoff for rate limiting.",
      },
      {
        label: "Datadog (v2 SDK)",
        desc: "Incidents, monitor states, and error logs are ingested via the official Datadog v2 API. Combined with New Relic data, this enables dual-source evidence capture for root cause analysis.",
      },
      {
        label: "TestRail",
        desc: "Test suites, sections, and cases are read from TestRail. The RCA Pipeline can write AI-generated test cases back to TestRail, create verification runs, and append to regression suites. Includes rate limit handling (429 backoff).",
      },
      {
        label: "Confluence",
        desc: "Operational runbooks and documentation are fetched from Confluence spaces. When credentials are configured, pages are queried via REST API; otherwise, static fallback data is used.",
      },
      {
        label: "Secrets Manager",
        desc: "Credentials can be sourced from environment variables, AWS Secrets Manager, or HashiCorp Vault. Automatic refresh capability handles credential rotation without restart. Configure via SECRETS_BACKEND env var.",
      },
    ],
  },
  {
    id: "understanding",
    icon: Brain,
    title: "How is data understood?",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    content: null,
    list: [
      {
        label: "AI-Powered Insights",
        desc: "Jira issues are analyzed by service domain (Authentication, Payments, Streaming, Content, etc.) using keyword classification. Each issue is assigned a priority, a recommended action, and an impact assessment. This drives the AI Insights Panel. Click 'Run RCA' to trigger the pipeline directly.",
      },
      {
        label: "Cost Impact Calculation ($)",
        desc: "Cost is computed using: Severity Daily Rate × Days Open. Rates: Critical = $500K/day, High = $150K/day, Medium = $25K/day. After 7 days, diminishing returns apply (30% rate). Formula: cost = (daily_rate × min(days, 7)) + (daily_rate × 0.3 × max(0, days - 7)). Revenue at Risk adds 50% buffer plus $50K per delay day. If Jira has an explicit cost_impact custom field, that value is used instead.",
      },
      {
        label: "Pareto Analysis (80/20 Rule)",
        desc: "Issues are grouped by severity and ranked by cost impact. The Pareto chart shows cumulative impact, validating whether the top 20% of issue categories drive 80% of operational impact -- helping teams focus on what matters most.",
      },
      {
        label: "Churn Risk Cohorts",
        desc: "Issues are classified into risk cohorts (Authentication Risk, Payment & Revenue Risk, Streaming Infrastructure, etc.). The worst-severity issue in each cohort determines the overall risk level, giving a service-area view of operational health.",
      },
      {
        label: "Streaming Quality of Experience",
        desc: "New Relic health status and Jira streaming-related issues are combined to compute buffering ratios, video start failure rates, and an Experience-Based Video Score (EBVS). Critical/high issues increase the computed degradation.",
      },
      {
        label: "RCA Pipeline (7-Step + Enterprise Features)",
        desc: "The automated Root Cause Analysis pipeline ingests a Jira ticket, captures evidence from New Relic + Datadog, AI-summarizes the root cause, matches against existing TestRail cases, generates new test cases if needed (with human review gate), analyzes blast radius, and closes the Jira ticket with a full RCA artifact. Includes idempotency, concurrency locking, retry/resume, and SHA-256 integrity hashing.",
      },
    ],
  },
  {
    id: "usage",
    icon: BarChart3,
    title: "How to use the dashboard",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    content: null,
    list: [
      {
        label: "Mission Control (Home)",
        desc: "Start every shift here. It surfaces the top-priority incident, system mode badge (mock/hybrid/live), pending approvals, recommended next action, and prioritized queue. Click any incident row to open its detail page.",
      },
      {
        label: "Incident Detail Page",
        desc: "Click any incident in the Mission Control queue to see full detail: decision scoring breakdown (operational severity, subscriber impact, business risk, confidence), ranked recommended actions with confidence/rationale/validation plan, incident timeline, governance reviews with approve/reject, blast radius graph, and verification status.",
      },
      {
        label: "Incident Timeline",
        desc: "Chronological event view showing Jira, New Relic, Datadog, and pipeline events for an incident. Each event shows source badge, timestamp, severity, and summary. Evidence completeness score indicates how much telemetry is available.",
      },
      {
        label: "Governance & Approvals",
        desc: "High-risk actions (rollback, restart) require human approval before execution. The governance panel shows pending reviews with SLA countdown, risk tier, and approve/reject buttons. All transitions are logged in a queryable audit trail. Access via the sidebar or within any incident detail page.",
      },
      {
        label: "Blast Radius Graph",
        desc: "Radial visualization of impacted services for an incident. The primary service is at the center; downstream/upstream dependencies are shown with confidence scores. Higher confidence (red) means stronger impact; lower (gray) means weaker coupling.",
      },
      {
        label: "Ops Chatbot",
        desc: "The chatbot in Mission Control uses tool-routed context (mission summary, incident detail, review queue) to answer operator questions with citations, tool trace, and quality score. Use it for 'what should we do next', approval checks, and incident stage lookups.",
      },
      {
        label: "Executive KPIs (Top Banner)",
        desc: "At-a-glance metrics: total issues, critical count, live integrations, and active production issues. Sparkline trends show 7-day movement. Click the refresh indicator to see real-time updates.",
      },
      {
        label: "AI Insights Panel",
        desc: "Click any insight card to open the corresponding Jira ticket in a new tab. Cards are sorted by priority (Critical first). Click 'Run RCA' to trigger the full pipeline. The recommended action and impact timeline are shown for each.",
      },
      {
        label: "Human Review Queue",
        desc: "View pending AI-generated test cases awaiting human approval. Shows SLA countdown (24h window), number of test cases, and approval button. Urgent items are highlighted when approaching/past deadline.",
      },
      {
        label: "Pareto Chart",
        desc: "The bar chart shows issue counts by severity, while the line shows cumulative percentage. Use this to validate the 80/20 rule and justify resource allocation.",
      },
      {
        label: "Streaming QoE",
        desc: "Monitor buffering ratios against the 2.5% target (green zone) and video start failures against the 1.0% target. The EBVS gauge gives a quick quality health indicator (0-10 scale).",
      },
      {
        label: "Issue Risk Cohorts",
        desc: "Horizontal bar chart groups issues by service area. Red = critical risk, amber = high risk, green = medium. Click to understand which service domains have the most active issues.",
      },
      {
        label: "Production Issues Table",
        desc: "Full table of all Jira issues with severity, status, cost impact, delay days, and RCA pipeline stage. Each row shows a color-coded badge for the pipeline stage. Click 'Run RCA' to trigger the pipeline for issues without an active RCA. All tables support pagination with configurable page sizes (10/25/50 per page).",
      },
      {
        label: "Export PDF",
        desc: "Click 'Export PDF' in the header to generate an executive report. The PDF includes KPI summary, top incidents with severity and cost impact, decision engine scoring, recommended actions, governance status, and integration health. Uses HTML-to-PDF fallback if Adobe SDK is not configured.",
      },
      {
        label: "Light / Dark Mode",
        desc: "Toggle between light and dark themes using the sun/moon icon in the header. All pages, sidebar, and components respond to the theme switch via CSS custom properties.",
      },
      {
        label: "RCA Pipeline (API)",
        desc: "Use POST /api/rca/pipeline/run from the API docs. For failed pipelines, use POST /api/rca/pipeline/resume to retry from the last stage. Results include AI summary, test case recommendations, blast radius, cycle time metrics, and integrity hash.",
      },
    ],
  },
  {
    id: "architecture",
    icon: Layers,
    title: "Technical Architecture",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    content: null,
    list: [
      {
        label: "Backend",
        desc: "FastAPI (Python 3.10+) with live integrations to Jira Cloud (PROD project, /search/jql POST), New Relic (GraphQL NerdGraph, account 7492750), Datadog (us5 site, SDK-based), TestRail (project 2, suite 11, sections 52/53 with service-based routing), and Confluence. SQLite for RCA audit trail (Postgres-compatible syntax). TTL caching layer. API key authentication via X-API-Key header.",
      },
      {
        label: "Frontend",
        desc: "React 18 + Vite + Tailwind CSS + Recharts. All components fetch live data from the FastAPI backend. Configurable API base URL via VITE_API_BASE_URL environment variable.",
      },
      {
        label: "Background Scheduler",
        desc: "APScheduler runs background tasks: SLA checker (every 5 min), proactive threshold monitoring (every 15 min), verification run polling (every 10 min), and heartbeat/dead-man switch (every minute).",
      },
      {
        label: "Real-time Events",
        desc: "Server-Sent Events (SSE) endpoint at /events/stream for push-based dashboard updates without polling.",
      },
      {
        label: "Concurrency Control",
        desc: "File-based locking prevents concurrent pipeline runs on the same service. Prevents race conditions during CDN events or simultaneous PROD tickets.",
      },
      {
        label: "Deployment",
        desc: "Docker multi-stage build (Dockerfile + docker-compose.yml). Frontend builds as static assets served alongside the Python backend.",
      },
      {
        label: "API Documentation",
        desc: "Interactive Swagger UI at http://localhost:8000/docs with all 70+ endpoints documented. ReDoc also available at /redoc.",
      },
    ],
  },
  {
    id: "security",
    icon: Shield,
    title: "Security & Configuration",
    color: "text-rose-400",
    bg: "bg-rose-500/10",
    border: "border-rose-500/30",
    content: null,
    list: [
      {
        label: "API Authentication",
        desc: "All MCP endpoints are protected by API key when API_SECRET_KEY is configured. Pass via X-API-Key header. Public paths (/health, /docs) are exempt.",
      },
      {
        label: "Secrets Management",
        desc: "Supports multiple backends: environment variables (default), AWS Secrets Manager, or HashiCorp Vault. Configure via SECRETS_BACKEND env var. Auto-refresh handles credential rotation.",
      },
      {
        label: "Artifact Integrity",
        desc: "Completed RCA artifacts include a SHA-256 hash for tamper evidence. Use GET /api/rca/pipeline/{id}/verify to confirm artifacts haven't been modified after Jira close. Critical for compliance/governance.",
      },
      {
        label: "Idempotency",
        desc: "All write operations use idempotency checks. Duplicate Jira webhooks or retried API calls won't create duplicate RCAs, test cases, or verification runs.",
      },
      {
        label: "Notifications",
        desc: "Slack webhooks and Jira comments notify reviewers when test cases are ready (REVIEW_PENDING). Configure SLACK_WEBHOOK_URL in .env. SLA breaches also trigger alerts.",
      },
    ],
  },
  {
    id: "enterprise",
    icon: GitBranch,
    title: "Enterprise Features (New)",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/30",
    content: null,
    list: [
      {
        label: "Retry/Resume Pipeline",
        desc: "POST /api/rca/pipeline/resume to recover from transient errors (NR timeout, TestRail 429, Datadog auth blip). State is preserved in SQLite. Supports up to 3 retries per RCA.",
      },
      {
        label: "Cycle Time Metrics",
        desc: "GET /api/rca/pipeline/{id}/metrics returns total cycle time, time-to-review, and review-wait hours. Stage timestamps are recorded for SLA tracking. Engineering leadership can track incident-level cycle times.",
      },
      {
        label: "Pipeline Health Endpoint",
        desc: "GET /api/rca/health returns scheduler status, heartbeat, metrics (success rate, avg cycle time), and pending review count. Use for monitoring the pipeline itself.",
      },
      {
        label: "Governance Runtime States",
        desc: "Actions transition through: proposed, awaiting_review, approved, rejected, expired, executed, failed. These states are auditable and exposed to operators as first-class runtime signals. The governance API (GET /api/governance/reviews, POST .../approve, POST .../reject) powers the UI panel.",
      },
      {
        label: "Decision Engine",
        desc: "Deterministic scoring model: operational_severity (35%), business_risk (30%), subscriber_impact (20%), confidence (15%). Produces ranked action recommendations with risk tier, owner, validation plan, and escalation path. No ML dependency for core flow.",
      },
      {
        label: "Dead-Man Switch",
        desc: "If the scheduler heartbeat hasn't updated in 5 minutes during an active incident, an alert fires. Ensures pipeline failures don't go unnoticed during P1s.",
      },
      {
        label: "Proactive Monitoring",
        desc: "Scheduler polls New Relic and Datadog thresholds every 15 minutes. Threshold breaches can auto-create Jira tickets before customers notice.",
      },
    ],
  },
  {
    id: "phase2",
    icon: Radio,
    title: "Phase 2 — AI-Augmented QA Intelligence",
    color: "text-teal-400",
    bg: "bg-teal-500/10",
    border: "border-teal-500/30",
    content: null,
    list: [
      {
        label: "2.1 Test Impact Analysis",
        desc: "Before deployment, analyze changed services against TestRail suite and dependency graph. Produces prioritized test run with ranked case IDs. POST /api/phase2/test-impact/analyze",
      },
      {
        label: "2.2 Automated Failure Triage",
        desc: "When regression run fails, auto-classify each failure: Genuine Regression (triggers RCA), Flaky (quarantine), Environment Issue (invalidate), Known Gap, or Stale Test. POST /api/phase2/triage/run",
      },
      {
        label: "2.3 Suite Hygiene",
        desc: "Weekly scan for: Stale cases (90+ days), Flaky (< 80% pass rate), Duplicates (> 85% similarity), Orphaned refs, Unverified pipeline-generated, Coverage gaps. POST /api/phase2/suite-hygiene/run",
      },
      {
        label: "2.4 Deployment Risk Score",
        desc: "Composite score (0-100) for deployment gating: RCA history (30%), pass rate (25%), coverage gaps (20%), stale regression (15%), unverified cases (10%). Returns tier: Low/Medium/High/Hold. POST /api/phase2/deployment-risk/score",
      },
      {
        label: "2.5 Cross-RCA Pattern Detection",
        desc: "Mines RCA history for patterns: temporal clusters, deployment correlation, service co-failure pairs, recurring root causes, MTTR trends. Generates actionable insights. POST /api/phase2/patterns/detect",
      },
      {
        label: "2.6 Alert-Driven Test Generation",
        desc: "Generate test cases from NR/DD alert definitions BEFORE anything breaks. An alert condition is a test spec. Gaps are auto-queued for review. POST /api/phase2/alert-tests/generate",
      },
      {
        label: "2.7 Test Effectiveness Scoring",
        desc: "Track per-case effectiveness: True Positives (caught bugs), False Positives (flaky), Missed Detections (passed during incidents). Precision/Recall/F1 over time. POST /api/phase2/effectiveness/calculate",
      },
    ],
  },
];

export function HelpModal({ open, onClose }: HelpModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-8 pb-8">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-700/50 bg-[#0D1117] shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 bg-[#0D1117]/95 backdrop-blur-sm border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-r from-[#0064FF] to-purple-600 p-2.5 rounded-xl">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                Help & Documentation
              </h2>
              <p className="text-xs text-slate-400">
                Paramount+ AI Operations Dashboard Guide
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <div
                key={section.id}
                className={`${section.bg} border ${section.border} rounded-xl p-5`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <Icon className={`w-5 h-5 ${section.color}`} />
                  <h3 className={`font-bold text-base ${section.color}`}>
                    {section.title}
                  </h3>
                </div>

                {section.content && (
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {section.content}
                  </p>
                )}

                {section.list && (
                  <div className="space-y-3">
                    {section.list.map((item, idx) => (
                      <div key={idx} className="flex gap-3">
                        <ArrowRight
                          className={`w-4 h-4 ${section.color} mt-0.5 flex-shrink-0`}
                        />
                        <div>
                          <span className="text-sm font-semibold text-white">
                            {item.label}
                          </span>
                          <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                            {item.desc}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 text-center">
            <p className="text-sm text-slate-400 mb-2">
              API Documentation & Swagger UI
            </p>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#0064FF] hover:bg-[#0052CC] rounded-lg text-sm font-medium text-white transition-colors"
            >
              Open API Docs
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
