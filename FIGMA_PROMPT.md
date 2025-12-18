# 🎨 Figma Dashboard Enhancement Prompt

Use this prompt in **Figma Make** or **Figma Design** to refine your dashboard:

---

## 📋 Prompt for Figma Make/Design

```
Create a modern, enterprise-grade operations dashboard for Paramount+ streaming platform with the following requirements:

## 🎯 Core Purpose
Real-time monitoring and AI-driven insights for streaming operations, combining:
- Subscriber churn prediction & retention
- Content ROI & production tracking
- Streaming QoE (Quality of Experience)
- Infrastructure health (APM)

## 📊 Key Sections (Priority Order)

### 1. Executive Summary (Top Banner)
- 4 KPI cards in a row:
  * Total Subscribers (with trend arrow)
  * Churn Risk Score (0-100, color-coded)
  * Revenue at Risk ($M)
  * Active Production Issues (count with severity indicator)
- Use Paramount+ brand colors: #0064FF (primary blue), #FF6B00 (accent orange)

### 2. AI Insights Panel (Prominent, Left Side)
- Title: "🤖 AI-Powered Recommendations"
- 3-4 actionable insights with priority badges (High/Medium/Low)
- Example: "80% of churn comes from 20% of content genres → Focus retention on Reality TV"
- Use card-based layout with icons

### 3. Churn Cohort Analysis (Center)
- Horizontal bar chart showing subscriber segments
- Color-coded by risk level (Red: High, Yellow: Medium, Green: Low)
- Show: Cohort name, subscriber count, churn probability %
- Interactive hover states

### 4. Production Issues Tracker (Right Side)
- Table/list view with:
  * Show name (linked)
  * Issue severity (Critical/High/Medium/Low with color dots)
  * Cost impact ($)
  * Days delayed
  * Status (Open/In Progress/Resolved)
- Filter buttons at top: All, Critical, High Priority

### 5. Streaming QoE Metrics (Bottom Left)
- 3 mini charts:
  * Buffering Rate (line chart, last 24h)
  * Video Start Failures (bar chart by CDN)
  * EBVS Rate (gauge/donut chart)
- Threshold indicators (green/yellow/red zones)

### 6. Infrastructure Health (Bottom Right)
- Service status grid:
  * API Gateway, Streaming Service, Auth Service, CDN
  * Each with: Response time (ms), Error rate (%), Status icon
- Use traffic light colors for health status

## 🎨 Design System

### Colors
- **Primary**: #0064FF (Paramount+ blue)
- **Accent**: #FF6B00 (orange for alerts)
- **Success**: #10B981 (green)
- **Warning**: #F59E0B (yellow)
- **Danger**: #EF4444 (red)
- **Background**: #F9FAFB (light gray)
- **Cards**: #FFFFFF with subtle shadow

### Typography
- **Headings**: Inter Bold, 24px-32px
- **Body**: Inter Regular, 14px-16px
- **Metrics**: Inter SemiBold, 18px-48px (for large numbers)

### Layout
- **Grid**: 12-column responsive grid
- **Spacing**: 8px base unit (multiples of 8)
- **Card Radius**: 12px
- **Shadows**: Subtle elevation (0 2px 8px rgba(0,0,0,0.08))

### Components
- Modern glassmorphism effect for AI panel
- Animated loading states
- Micro-interactions on hover
- Status badges with icons
- Responsive breakpoints: Desktop (1920px), Tablet (1024px), Mobile (375px)

## 🚀 Special Features
1. **Dark Mode Toggle** (top-right corner)
2. **Real-time Data Indicator** (pulsing dot when live)
3. **Export to PDF** button (top-right)
4. **Date Range Picker** (last 7/30/90 days)
5. **Refresh Button** with last updated timestamp

## 📱 Responsive Behavior
- Desktop: 3-column layout
- Tablet: 2-column layout, stack AI panel on top
- Mobile: Single column, prioritize KPIs and AI insights

## 🎭 Inspiration
Think: Netflix admin dashboard + Datadog monitoring + Tableau analytics
Modern, clean, data-dense but not cluttered, enterprise-ready
```

---

## 🔧 How to Use This Prompt

### Option 1: Figma Make (Recommended for Speed)
1. Go to [Figma Make](https://www.figma.com/make)
2. Paste the prompt above
3. Click "Generate"
4. Review and iterate with follow-up prompts like:
   - "Make the AI insights panel more prominent"
   - "Add more spacing between cards"
   - "Use a darker shade of blue for the primary color"

### Option 2: Manual Design in Figma
1. Create a new file in Figma Design
2. Use the prompt as a specification document
3. Build components manually using the design system specs
4. Leverage Figma's Auto Layout and Components

### Option 3: Enhance Existing Dashboard
1. Open your current dashboard: [Paramount+ Operations Dashboard](https://www.figma.com/make/plRON3L0H4q0tfb4bnEhM5/Paramount--Operations-Dashboard?t=K0eEpL0F3TmVTWyj-1)
2. Click "Edit" or "Remix"
3. Use Figma Make's "Edit with AI" feature
4. Paste sections of the prompt to refine specific areas

---

## 🎯 Iteration Prompts (After Initial Generation)

### For Better Visual Hierarchy
```
Increase the prominence of the AI Insights panel - make it larger with a gradient background (blue to purple). Add a subtle glow effect. Move it to the top-left, above the churn cohorts.
```

### For More Data Density
```
Add a mini timeline chart to each KPI card showing the last 7 days trend. Make the production issues table more compact with smaller row height.
```

### For Better Branding
```
Apply Paramount+ brand guidelines more strongly - use the mountain logo as a watermark in the background. Add the Paramount+ wordmark to the top-left corner.
```

### For Demo Impact
```
Add animated state transitions - show loading skeletons, then data populating. Add a "Live Demo Mode" toggle that simulates real-time data updates with smooth animations.
```

---

## 📦 Export Options

After finalizing the design:

1. **Export to React** (Figma Make):
   - Click "Export" → "Code" → "React"
   - Download ZIP
   - Unzip to `dashboard/` directory

2. **Export Assets** (Figma Design):
   - Select frames → Export → PNG/SVG
   - Use for documentation and presentations

3. **Share Prototype**:
   - Click "Share" → "Get link"
   - Enable "Anyone with the link can view"
   - Add to README and presentation deck

---

## ✅ Hackathon Checklist

- [ ] Dashboard has all 6 key sections
- [ ] AI insights panel is prominent and actionable
- [ ] Color scheme matches Paramount+ branding
- [ ] Responsive design for mobile/tablet/desktop
- [ ] Dark mode toggle implemented
- [ ] Real-time data indicator visible
- [ ] Production issues linked to JIRA (in React code)
- [ ] Churn cohorts show risk levels clearly
- [ ] QoE metrics have threshold indicators
- [ ] Infrastructure health uses traffic light colors
- [ ] Export to React code works without errors
- [ ] Dashboard runs locally at http://localhost:5173
- [ ] README updated with Figma link
- [ ] Demo video shows dashboard in action

---

**Current Dashboard:** [View on Figma](https://www.figma.com/make/plRON3L0H4q0tfb4bnEhM5/Paramount--Operations-Dashboard?t=K0eEpL0F3TmVTWyj-1)


