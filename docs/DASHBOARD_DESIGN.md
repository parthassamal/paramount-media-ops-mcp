# Paramount+ Operations Dashboard - Design System

## 🎨 Figma Design

### Live Prototype

<a href="https://www.figma.com/make/plRON3L0H4q0tfb4bnEhM5/Paramount--Operations-Dashboard?t=K0eEpL0F3TmVTWyj-1" target="_blank">
  <img src="https://img.shields.io/badge/Figma-View%20Dashboard-F24E1E?style=for-the-badge&logo=figma&logoColor=white" alt="View Figma Dashboard"/>
</a>

**File ID:** `plRON3L0H4q0tfb4bnEhM5`

### Design File

- **Figma Make File**: [Paramount+ Operations Dashboard](https://www.figma.com/make/plRON3L0H4q0tfb4bnEhM5/Paramount--Operations-Dashboard?t=K0eEpL0F3TmVTWyj-1)
- **Exported React Code**: `dashboard/` directory (running at http://localhost:5173)

---

## 🔗 Figma API Integration (Enterprise)

With Figma Enterprise, you can programmatically access design tokens and sync with the MCP server.

### Setup

1. **Get Personal Access Token**: Figma → Settings → Account → Personal access tokens
2. **Configure Environment**:

```bash
# .env file
FIGMA_ENABLED=true
FIGMA_ACCESS_TOKEN=your-personal-access-token
FIGMA_FILE_ID=plRON3L0H4q0tfb4bnEhM5
```

### Using the Figma Client

```python
from mcp.integrations import FigmaClient

# Initialize client
figma = FigmaClient()

# Get design tokens
tokens = figma.get_design_tokens("your-file-id")
print(tokens["colors"])  # List of color tokens

# Get complete design system
design_system = figma.get_dashboard_design_system()
print(design_system["components"])  # Dashboard components

# Export to CSS variables
css = figma.export_to_css_variables()
print(css)
# :root {
#   --color-primary-blue: #0066FF;
#   --color-success-green: #34D399;
#   ...
# }

# Access Enterprise Variables API
variables = figma.get_local_variables("your-file-id")
for var in variables:
    print(f"{var.name}: {var.value_by_mode}")
```

### Enterprise Features

| Feature | Description | API Endpoint |
|---------|-------------|--------------|
| **Variables API** | Design tokens as variables with modes (light/dark) | `/files/{id}/variables/local` |
| **Team Libraries** | Shared components across projects | `/teams/{id}/components` |
| **Branching** | Version control for design files | `/files/{id}/branches` |
| **Comments API** | Design feedback and annotations | `/files/{id}/comments` |
| **Analytics** | Usage tracking for components | Enterprise Dashboard |

### Figma MCP Server

Figma now offers native MCP support! You can connect Figma directly to AI coding tools:

```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "@anthropic/figma-mcp-server"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "your-token"
      }
    }
  }
}
```

Learn more: [Figma MCP](https://www.figma.com/)

---

## 📊 Dashboard Overview

The Paramount+ Operations Dashboard provides real-time visibility into streaming operations, powered by the MCP server's Pareto-driven intelligence.

### Dashboard Sections

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PARAMOUNT+ MEDIA OPERATIONS DASHBOARD                      🔧 Settings    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ 📊 CHURN     │  │ 🎬 PRODUCTION│  │ 📺 STREAMING │  │ 💬 COMPLAINTS│    │
│  │   $965M      │  │   1 Critical │  │   3.5% Buff  │  │   847 Open   │    │
│  │   at risk    │  │   issue      │  │   ratio      │  │   tickets    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │ PARETO ANALYSIS (80/20)         │  │ TOP PRIORITIES                  │  │
│  │                                 │  │                                 │  │
│  │  Churn: ████████████░░░ 77%     │  │  1. Content library gaps $45M   │  │
│  │  Prod:  ████████░░░░░░░ 72%     │  │  2. Streaming quality    $25M   │  │
│  │  Compl: ██████░░░░░░░░░ 64%     │  │  3. Production delays    $15M   │  │
│  │                                 │  │                                 │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ AT-RISK COHORTS                                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Cohort                      │ Size    │ Risk  │ Impact   │ Action  │   │
│  │ High-Value Serial Churners  │ 44,100  │ 85%   │ $61.7M   │ [View]  │   │
│  │ Price-Sensitive Millennials │ 33,800  │ 72%   │ $9.5M    │ [View]  │   │
│  │ Tech-Frustrated Adopters    │ 15,400  │ 68%   │ $5.4M    │ [View]  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │ STREAMING HEALTH (Conviva)      │  │ APM METRICS (NewRelic)         │  │
│  │                                 │  │                                │  │
│  │  Plays: 160K    Bitrate: 6.8Mb  │  │  Response: 145ms   Apdex: 0.77 │  │
│  │  Buffering: 3.5% ⚠️             │  │  Errors: 1.58% ⚠️              │  │
│  │  VSF: 2.8%      EBVS: 2.8%      │  │  Throughput: 20K rpm           │  │
│  │                                 │  │                                │  │
│  └──────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Design System

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| **Paramount Blue** | `#0066FF` | Primary actions, headers |
| **Deep Navy** | `#1A1F36` | Background, dark mode |
| **Success Green** | `#34D399` | Healthy metrics, success states |
| **Warning Yellow** | `#FBBF24` | Warning states, attention needed |
| **Critical Red** | `#EF4444` | Critical alerts, high-risk |
| **Neutral Gray** | `#6B7280` | Secondary text, borders |

### Typography

| Style | Font | Size | Weight | Usage |
|-------|------|------|--------|-------|
| **H1** | Inter | 32px | Bold | Page titles |
| **H2** | Inter | 24px | Semibold | Section headers |
| **H3** | Inter | 18px | Medium | Card titles |
| **Body** | Inter | 14px | Regular | Content text |
| **Caption** | Inter | 12px | Regular | Labels, metadata |
| **Metric** | JetBrains Mono | 28px | Bold | KPI values |

### Components

#### 1. KPI Card
```
┌─────────────────┐
│  📊 METRIC      │  ← Icon + Label
│     $965M       │  ← Large value
│     at risk     │  ← Description
│  ▲ 12% vs last  │  ← Trend indicator
└─────────────────┘
```

#### 2. Pareto Bar
```
████████████░░░░░ 77%
└── Filled ──┘└ Empty ┘
```

#### 3. Priority List
```
┌─ Priority Indicator (color-coded)
│  ┌─────────────────────────────────┐
●  │ Content library gaps    │ $45M │
●  │ Streaming quality       │ $25M │
○  │ Production delays       │ $15M │
   └─────────────────────────────────┘
```

#### 4. Status Badge
```
[● Healthy]  [⚠ Warning]  [✕ Critical]
   Green        Yellow        Red
```

---

## 📱 Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| **Desktop** | ≥1280px | 4-column grid |
| **Laptop** | ≥1024px | 3-column grid |
| **Tablet** | ≥768px | 2-column grid |
| **Mobile** | <768px | 1-column stack |

---

## 🖼️ Figma Embed

To embed the Figma prototype in presentations or web pages:

### HTML Embed
```html
<iframe 
  style="border: 1px solid rgba(0, 0, 0, 0.1);" 
  width="800" 
  height="450" 
  src="https://www.figma.com/embed?embed_host=share&url=https://www.figma.com/proto/YOUR_FIGMA_FILE_ID/Paramount-Media-Ops-Dashboard" 
  allowfullscreen>
</iframe>
```

### Markdown Link
```markdown
[![Figma Prototype](https://img.shields.io/badge/Figma-Prototype-F24E1E?logo=figma)](https://www.figma.com/proto/YOUR_FIGMA_FILE_ID)
```

---

## 📐 Screen Specifications

### 1. Executive Dashboard
- **Purpose**: High-level overview for executives
- **Key Metrics**: Total churn risk, Pareto validation, top 3 priorities
- **Update Frequency**: Real-time

### 2. Churn Analysis
- **Purpose**: Deep dive into subscriber churn
- **Key Metrics**: Cohort breakdown, risk scores, financial impact
- **Features**: Drill-down to individual cohorts

### 3. Production Operations
- **Purpose**: Track content production issues
- **Key Metrics**: Critical issues, delays, cost overruns
- **Integration**: JIRA issue data

### 4. Streaming Health
- **Purpose**: Monitor streaming QoE
- **Key Metrics**: Buffering, VSF, bitrate, concurrent plays
- **Integration**: Conviva metrics

### 5. Campaign Management
- **Purpose**: Track retention campaigns
- **Key Metrics**: Conversion rates, ROI, budget utilization
- **Features**: Campaign creation wizard

---

## 🔗 Figma Resources

### Design File Structure
```
📁 Paramount Media Ops Dashboard
├── 📄 Cover
├── 📁 Design System
│   ├── Colors
│   ├── Typography
│   └── Components
├── 📁 Screens
│   ├── Executive Dashboard
│   ├── Churn Analysis
│   ├── Production Ops
│   ├── Streaming Health
│   └── Campaigns
├── 📁 Prototype Flows
│   ├── Main Navigation
│   └── Drill-down Interactions
└── 📁 Assets
    ├── Icons
    └── Illustrations
```

### How to Use

1. **Open Figma File**: Click the Figma link above
2. **Duplicate to Edit**: File → Duplicate to your drafts
3. **View Prototype**: Click ▶️ Play button in top-right
4. **Export Assets**: Select element → Export (bottom-right panel)

---

## 🎥 Demo Video Integration

For the hackathon demo video, use the Figma prototype to show:

1. **Dashboard Overview** (0:00-0:30)
   - Navigate through main dashboard
   - Highlight Pareto analysis visualization

2. **Drill-down Flow** (0:30-1:00)
   - Click on a churn cohort
   - Show root cause analysis

3. **Campaign Creation** (1:00-1:30)
   - Create retention campaign
   - Show projected ROI

4. **API Integration** (1:30-2:00)
   - Show live data from MCP server
   - Demonstrate real-time updates

---

## 📋 Checklist for Figma Design

- [ ] Create Figma account and new file
- [ ] Set up design system (colors, typography)
- [ ] Design Executive Dashboard screen
- [ ] Design Churn Analysis screen
- [ ] Design Production Ops screen
- [ ] Design Streaming Health screen
- [ ] Add interactive prototype links
- [ ] Export presentation assets
- [ ] Record demo walkthrough
- [ ] Update this doc with actual Figma URL

---

**Design Contact**: Paramount Media Operations Team

*Last Updated: December 2025*

