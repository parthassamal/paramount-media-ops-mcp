#!/usr/bin/env python3
"""
Seed realistic test data into Jira, TestRail, New Relic, and Datadog.

Run: python scripts/seed_test_data.py
"""

import os
import sys
import json
import time
import random
import requests
import httpx
from datetime import datetime, timedelta
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# =============================================================================
# CONFIG
# =============================================================================
JIRA_URL = os.environ.get("JIRA_API_URL", "https://paramounthackathon.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_API_EMAIL", "")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT = os.environ.get("JIRA_PROJECT_KEY", "PROD")

NR_API_KEY = os.environ.get("NEWRELIC_API_KEY", "")
NR_ACCOUNT_ID = os.environ.get("NEWRELIC_ACCOUNT_ID", "")

DD_API_KEY = os.environ.get("DD_API_KEY", "")
DD_SITE = os.environ.get("DD_SITE", "us5.datadoghq.com")

TR_URL = os.environ.get("TESTRAIL_URL", "https://rca.testrail.io")
TR_EMAIL = os.environ.get("TESTRAIL_EMAIL", "")
TR_API_KEY = os.environ.get("TESTRAIL_API_KEY", "")


def banner(msg):
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}")


# =============================================================================
# 1. JIRA -- Create Production Incident Tickets
# =============================================================================
JIRA_ISSUES = [
    {
        "summary": "P1 - Auth service returning 500 on login for Paramount+ mobile app",
        "description": "**Impact**: ~45,000 users unable to log in on iOS and Android since 06:15 UTC.\n\n**Error**: `NullPointerException` in `AuthTokenService.validateSession()` at line 342.\n\n**Stack Trace**:\n```\njava.lang.NullPointerException\n  at com.paramount.auth.AuthTokenService.validateSession(AuthTokenService.java:342)\n  at com.paramount.auth.LoginController.handleLogin(LoginController.java:87)\n```\n\n**Metrics**:\n- Error rate: 12.5% (normal: 0.1%)\n- P99 latency: 8,200ms (normal: 150ms)\n- Affected regions: US-East, US-West\n\n**Reproduction Steps**:\n1. Open Paramount+ mobile app\n2. Tap Sign In\n3. Enter valid credentials\n4. Observe 500 error",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Highest"},
        "labels": ["production-incident", "P1", "auth-service", "mobile"]
    },
    {
        "summary": "P1 - CDN buffering ratio spike to 8.2% during NFL playoff streaming",
        "description": "**Impact**: Buffering ratio spiked from 1.2% to 8.2% during NFL AFC Championship game.\n\n**Affected Users**: ~2.1M concurrent viewers experiencing degraded playback.\n\n**Root Cause Investigation**:\n- CDN edge nodes in US-Central saturated at 95% capacity\n- Origin shield cache miss rate increased from 2% to 34%\n- Transcoding pipeline backed up with 45-minute queue\n\n**Metrics**:\n- Buffering ratio: 8.2% (SLA: <2%)\n- Video start failures: 4.7% (SLA: <1%)\n- Average bitrate dropped from 7.2 Mbps to 2.1 Mbps\n- Concurrent streams: 2.1M (expected: 1.8M)\n\n**Business Impact**: Estimated $3.2M in churn risk from degraded experience.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Highest"},
        "labels": ["production-incident", "P1", "streaming", "CDN", "NFL"]
    },
    {
        "summary": "P2 - Payment processing failures for annual subscription renewals",
        "description": "**Impact**: 12% of annual subscription renewals failing with payment gateway timeout.\n\n**Error**: `PaymentGatewayTimeoutException` after 30s - Stripe webhook not responding.\n\n**Affected**: ~8,500 renewal attempts in the last 4 hours.\n\n**Revenue Impact**: $127,500 in delayed renewals (avg $15/subscription).\n\n**Logs**:\n```\n2026-03-24T10:15:23Z ERROR payment-service: Stripe webhook timeout after 30000ms\n2026-03-24T10:15:23Z ERROR payment-service: Retry 3/3 failed for subscription_id=sub_1234\n2026-03-24T10:15:24Z WARN  payment-service: Moving to dead letter queue: 847 pending\n```",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["production-incident", "P2", "payment-service", "stripe"]
    },
    {
        "summary": "P2 - Recommendation engine serving stale content for new subscribers",
        "description": "**Impact**: New subscribers (< 7 days) receiving generic recommendations instead of personalized onboarding flow.\n\n**Root Cause**: Redis cache TTL misconfigured during last deployment - set to 72h instead of 15min for user-profile lookups.\n\n**Affected Users**: ~23,000 new signups in past 3 days.\n\n**Business Impact**:\n- New user engagement rate dropped 34%\n- Day-7 retention for affected cohort: 41% (expected: 68%)\n- Estimated churn risk: $4.1M annually if unresolved",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["production-incident", "P2", "recommendation-engine", "redis"]
    },
    {
        "summary": "P2 - DRM license acquisition failing for 4K HDR content on Roku devices",
        "description": "**Impact**: Roku Ultra and Streaming Stick 4K users unable to play any 4K HDR content.\n\n**Error**: `DRM_LICENSE_ERROR: Widevine L1 handshake failed (error code: 6007)`\n\n**Affected**: ~180,000 Roku 4K device sessions per day.\n\n**Timeline**:\n- 03:00 UTC: Widevine license server certificate rotated (scheduled)\n- 03:15 UTC: First error reports from Roku devices\n- 04:30 UTC: Error rate stabilized at 100% for Roku 4K HDR requests\n\n**Workaround**: Users can watch SD/HD content. 4K HDR completely blocked.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["production-incident", "P2", "DRM", "roku", "4K-HDR"]
    },
    {
        "summary": "P3 - Search service returning duplicate results for show titles",
        "description": "**Impact**: Search results showing duplicate entries for ~15% of show titles.\n\n**Root Cause**: Elasticsearch index rebuild created duplicate documents due to missing dedup step in the content ingestion pipeline.\n\n**Example**: Searching 'Star Trek' returns 3 duplicate entries for 'Star Trek: Discovery'.\n\n**Affected**: All platforms, all regions. UX impact only - no playback issues.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Medium"},
        "labels": ["production-incident", "P3", "search-service", "elasticsearch"]
    },
    {
        "summary": "P3 - Subtitles out of sync by 2-3 seconds on Samsung Smart TVs",
        "description": "**Impact**: Closed captions and subtitles displaying 2-3 seconds behind audio on Samsung Tizen OS 6.0+ devices.\n\n**Affected Content**: All VOD content with embedded WebVTT subtitles.\n\n**Device Scope**: Samsung Smart TVs manufactured 2022+\n\n**User Reports**: 847 support tickets in past 48 hours.\n\n**Suspected Cause**: Tizen 6.0 media pipeline timing change - Samsung pushed a firmware update last week.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Medium"},
        "labels": ["production-incident", "P3", "subtitles", "samsung", "tizen"]
    },
    {
        "summary": "P1 - Content catalog API returning empty responses - homepage blank",
        "description": "**Impact**: Paramount+ homepage showing blank/empty state for all users across all platforms.\n\n**Duration**: Started 14:23 UTC, ongoing.\n\n**Error**: Content catalog API returning `{\"items\": [], \"total\": 0}` for all browse/discover endpoints.\n\n**Root Cause**: MongoDB primary node failover to a replica that was 6 hours behind in replication.\n\n**Metrics**:\n- API error rate: 0% (responses are valid JSON, just empty)\n- Homepage engagement: dropped 98%\n- App store ratings: 2 negative reviews already mentioning 'empty app'\n\n**Business Impact**: CRITICAL - every user sees an empty app.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Highest"},
        "labels": ["production-incident", "P1", "content-catalog", "mongodb", "homepage"]
    },
    {
        "summary": "P2 - Live sports stream latency 45-60 seconds behind broadcast",
        "description": "**Impact**: Paramount+ live sports streams running 45-60 seconds behind traditional broadcast.\n\n**Affected Events**: UEFA Champions League, March Madness, Serie A\n\n**User Complaints**: Social media spoilers ruining experience. 1,200+ support tickets.\n\n**Technical Details**:\n- Encoder pipeline adding 15s extra latency since transcoding upgrade\n- CDN segment duration increased from 2s to 6s chunks\n- Total glass-to-glass: ~58 seconds (target: <15s)\n\n**Revenue Risk**: Sports subscribers are highest ARPU segment ($25/mo avg).",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["production-incident", "P2", "live-sports", "latency", "transcoding"]
    },
    {
        "summary": "P3 - Analytics event pipeline dropping 5% of playback start events",
        "description": "**Impact**: 5% of `playback_start` events not reaching the analytics data warehouse.\n\n**Root Cause**: Kafka consumer group rebalancing too aggressively during peak hours.\n\n**Business Impact**: Inaccurate viewership metrics for content licensing negotiations.\n\n**Affected Period**: Last 14 days of data has gaps.\n\n**Metrics**:\n- Expected daily events: ~45M\n- Actual received: ~42.75M\n- Gap: ~2.25M events/day",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Medium"},
        "labels": ["production-incident", "P3", "analytics-pipeline", "kafka"]
    },
    {
        "summary": "P2 - Profile switching causing watch history merge between family members",
        "description": "**Impact**: When switching between profiles on shared accounts, watch history and 'Continue Watching' from other profiles bleeds through.\n\n**Affected**: ~340,000 multi-profile households.\n\n**Privacy Concern**: Kids profile showing parent content recommendations.\n\n**Root Cause**: Session cookie not being invalidated on profile switch - cached user context persists for 5 minutes.\n\n**Compliance Risk**: Potential COPPA violation for kids profiles showing mature content titles.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["production-incident", "P2", "profile-service", "privacy", "COPPA"]
    },
    {
        "summary": "P3 - Push notification service sending duplicate alerts",
        "description": "**Impact**: Users receiving 2-3 duplicate push notifications for new episode releases.\n\n**Root Cause**: Notification dedup service Redis cluster split-brain after network partition.\n\n**Scale**: ~4.2M duplicate notifications sent in past 24 hours.\n\n**User Impact**: Annoyance factor - 156 app store reviews mentioning spam notifications.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Medium"},
        "labels": ["production-incident", "P3", "notification-service", "redis"]
    },
    {
        "summary": "Task - Implement circuit breaker for payment gateway integration",
        "description": "After the P2 payment processing incident, we need to implement a circuit breaker pattern for the Stripe integration.\n\n**Requirements**:\n- Open circuit after 5 consecutive failures\n- Half-open after 30 seconds\n- Fallback to queued retry for failed transactions\n- Alert on circuit state change\n\n**Acceptance Criteria**:\n- [ ] Circuit breaker wraps all Stripe API calls\n- [ ] Metrics dashboard shows circuit state\n- [ ] Runbook updated with circuit breaker recovery steps",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["engineering", "reliability", "payment-service"]
    },
    {
        "summary": "Task - CDN capacity planning for upcoming Halo Season 3 premiere",
        "description": "**Event**: Halo Season 3 premiere - March 28, 2026\n\n**Expected Peak**: 3.5M concurrent streams (based on S2 premiere + 40% growth)\n\n**Action Items**:\n- [ ] Pre-warm CDN edge caches in top 20 markets\n- [ ] Scale origin shield to 4x normal capacity\n- [ ] Pre-position 4K HDR assets on edge nodes\n- [ ] War room scheduled 2 hours before premiere\n- [ ] Rollback plan for transcoding pipeline\n\n**Budget**: Pre-approved $45K for burst CDN capacity.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["capacity-planning", "CDN", "halo", "premiere"]
    },
    {
        "summary": "P2 - Geo-restriction bypass detected - content leaking to blocked regions",
        "description": "**Impact**: Premium content (NFL, Champions League) accessible in regions where Paramount+ doesn't hold distribution rights.\n\n**Detection**: Rights holder flagged 12,000 streams from blocked countries.\n\n**Root Cause**: VPN detection service (MaxMind) database update missed - running on data 3 weeks old.\n\n**Legal Risk**: Potential breach of content licensing agreements. Rights holders may invoke penalty clauses.\n\n**Immediate Action**: Manual IP blocklist deployed for known VPN ranges.",
        "issuetype": {"name": "Task"},
        "priority": {"name": "High"},
        "labels": ["production-incident", "P2", "geo-restriction", "licensing", "legal"]
    },
]


def seed_jira():
    banner("SEEDING JIRA")
    if not JIRA_TOKEN:
        print("  SKIP: No JIRA_API_TOKEN configured")
        return

    auth = (JIRA_EMAIL, JIRA_TOKEN)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    base_url = f"{JIRA_URL}/rest/api/3"

    # Check project exists
    resp = requests.get(f"{base_url}/project/{JIRA_PROJECT}", auth=auth, headers=headers, timeout=15)
    if resp.status_code != 200:
        print(f"  ERROR: Project {JIRA_PROJECT} not found ({resp.status_code})")
        print(f"  Response: {resp.text[:200]}")
        # Try to find available projects
        resp2 = requests.get(f"{base_url}/project", auth=auth, headers=headers, timeout=15)
        if resp2.status_code == 200:
            projects = resp2.json()
            print(f"  Available projects: {[p['key'] for p in projects]}")
        return

    created = 0
    for issue_data in JIRA_ISSUES:
        payload = {
            "fields": {
                "project": {"key": JIRA_PROJECT},
                "summary": issue_data["summary"],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": issue_data["description"]}]
                        }
                    ]
                },
                "issuetype": issue_data["issuetype"],
                "priority": issue_data.get("priority", {"name": "Medium"}),
                "labels": issue_data.get("labels", [])
            }
        }

        resp = requests.post(f"{base_url}/issue", auth=auth, headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            key = resp.json().get("key", "?")
            print(f"  Created: {key} - {issue_data['summary'][:60]}")
            created += 1
        else:
            print(f"  FAILED ({resp.status_code}): {issue_data['summary'][:50]}")
            print(f"    {resp.text[:200]}")
        time.sleep(0.3)

    print(f"\n  Total created: {created}/{len(JIRA_ISSUES)}")


# =============================================================================
# 2. TESTRAIL -- Create Suites, Sections, Test Cases
# =============================================================================
def _tr(method, endpoint, payload=None):
    url = f"{TR_URL}/index.php?/api/v2/{endpoint}"
    auth = (TR_EMAIL, TR_API_KEY)
    headers = {"Content-Type": "application/json"}
    if method == "GET":
        resp = requests.get(url, auth=auth, headers=headers, timeout=15)
    else:
        resp = requests.post(url, auth=auth, headers=headers, json=payload, timeout=15)
    return resp


def seed_testrail():
    banner("SEEDING TESTRAIL")
    if not TR_API_KEY:
        print("  SKIP: No TESTRAIL_API_KEY configured")
        return

    project_id = int(os.environ.get("TESTRAIL_PROJECT_ID", "1"))

    # Create a new project with multiple suites mode
    resp = _tr("POST", "add_project", {
        "name": "Paramount+ Streaming Platform",
        "announcement": "Production test coverage for Paramount+ streaming services",
        "show_announcement": True,
        "suite_mode": 3  # Multiple test suites
    })
    if resp.status_code in (200, 201):
        project_id = resp.json()["id"]
        print(f"  Created project ID: {project_id}")
    else:
        print(f"  Project create failed ({resp.status_code}): {resp.text[:200]}")
        # Fall back to existing project
        resp2 = _tr("GET", f"get_project/{project_id}")
        if resp2.status_code != 200:
            print("  No usable project found, skipping TestRail")
            return
        print(f"  Using existing project {project_id}")

    # Create suites
    suites = [
        {"name": "Streaming Playback Regression", "description": "Core playback regression tests for all platforms"},
        {"name": "Authentication & Authorization", "description": "Login, SSO, profile management, session handling"},
        {"name": "Payment & Subscription", "description": "Billing, renewals, upgrades, cancellation flows"},
        {"name": "Content Discovery & Search", "description": "Browse, search, recommendations, catalog"},
        {"name": "Live Sports & Events", "description": "Live streaming, DVR, low-latency, multi-cam"},
        {"name": "RCA Pipeline - AI Generated", "description": "AI-generated regression cases from production incidents"},
    ]

    created_suites = {}
    for suite_data in suites:
        resp = _tr("POST", f"add_suite/{project_id}", suite_data)
        if resp.status_code in (200, 201):
            s = resp.json()
            created_suites[suite_data["name"]] = s["id"]
            print(f"  Suite: {s['id']} - {suite_data['name']}")
        else:
            print(f"  Suite FAILED: {suite_data['name']} - {resp.text[:150]}")
        time.sleep(0.2)

    # Create sections and test cases for each suite
    test_cases_by_suite = {
        "Streaming Playback Regression": {
            "sections": [
                {
                    "name": "Video Playback - VOD",
                    "cases": [
                        {"title": "Verify SD playback starts within 3 seconds on WiFi", "priority_id": 2, "type_id": 4},
                        {"title": "Verify HD 1080p playback maintains stable bitrate", "priority_id": 2, "type_id": 4},
                        {"title": "Verify 4K HDR playback on supported devices", "priority_id": 1, "type_id": 4},
                        {"title": "Verify adaptive bitrate switching on bandwidth change", "priority_id": 1, "type_id": 4},
                        {"title": "Verify playback resume from last position", "priority_id": 2, "type_id": 4},
                        {"title": "Verify subtitles display correctly during playback", "priority_id": 2, "type_id": 4},
                        {"title": "Verify audio track switching (5.1, stereo, AD)", "priority_id": 3, "type_id": 4},
                        {"title": "Verify DRM license acquisition for Widevine L1", "priority_id": 1, "type_id": 4},
                    ]
                },
                {
                    "name": "Video Playback - Live",
                    "cases": [
                        {"title": "Verify live stream starts within 5 seconds", "priority_id": 1, "type_id": 4},
                        {"title": "Verify live-to-VOD transition after event ends", "priority_id": 2, "type_id": 4},
                        {"title": "Verify DVR rewind during live event", "priority_id": 2, "type_id": 4},
                        {"title": "Verify glass-to-glass latency < 15 seconds", "priority_id": 1, "type_id": 4},
                    ]
                },
                {
                    "name": "Platform - Roku",
                    "cases": [
                        {"title": "Verify playback on Roku Ultra (4K HDR)", "priority_id": 1, "type_id": 4},
                        {"title": "Verify playback on Roku Streaming Stick 4K", "priority_id": 2, "type_id": 4},
                        {"title": "Verify Roku deep link launches correct content", "priority_id": 3, "type_id": 4},
                    ]
                }
            ]
        },
        "Authentication & Authorization": {
            "sections": [
                {
                    "name": "Login Flows",
                    "cases": [
                        {"title": "Verify email/password login succeeds with valid credentials", "priority_id": 1, "type_id": 4},
                        {"title": "Verify login fails with incorrect password", "priority_id": 1, "type_id": 4},
                        {"title": "Verify SSO login via Apple ID", "priority_id": 2, "type_id": 4},
                        {"title": "Verify SSO login via Google", "priority_id": 2, "type_id": 4},
                        {"title": "Verify session persists across app restart", "priority_id": 2, "type_id": 4},
                        {"title": "Verify concurrent stream limit enforcement (3 devices)", "priority_id": 1, "type_id": 4},
                    ]
                },
                {
                    "name": "Profile Management",
                    "cases": [
                        {"title": "Verify profile creation with avatar selection", "priority_id": 3, "type_id": 4},
                        {"title": "Verify profile switching clears previous session state", "priority_id": 1, "type_id": 4},
                        {"title": "Verify kids profile content filtering", "priority_id": 1, "type_id": 4},
                        {"title": "Verify parental controls PIN enforcement", "priority_id": 1, "type_id": 4},
                    ]
                }
            ]
        },
        "Payment & Subscription": {
            "sections": [
                {
                    "name": "Subscription Management",
                    "cases": [
                        {"title": "Verify monthly subscription purchase flow", "priority_id": 1, "type_id": 4},
                        {"title": "Verify annual subscription renewal processing", "priority_id": 1, "type_id": 4},
                        {"title": "Verify plan upgrade from Essential to Paramount+ with SHOWTIME", "priority_id": 2, "type_id": 4},
                        {"title": "Verify cancellation flow with retention offer", "priority_id": 1, "type_id": 4},
                        {"title": "Verify payment method update", "priority_id": 2, "type_id": 4},
                        {"title": "Verify free trial to paid conversion", "priority_id": 1, "type_id": 4},
                    ]
                }
            ]
        },
        "Content Discovery & Search": {
            "sections": [
                {
                    "name": "Search",
                    "cases": [
                        {"title": "Verify search returns relevant results for show titles", "priority_id": 1, "type_id": 4},
                        {"title": "Verify search autocomplete suggestions", "priority_id": 3, "type_id": 4},
                        {"title": "Verify search handles special characters", "priority_id": 3, "type_id": 4},
                        {"title": "Verify voice search on mobile", "priority_id": 3, "type_id": 4},
                    ]
                },
                {
                    "name": "Recommendations",
                    "cases": [
                        {"title": "Verify personalized recommendations for existing users", "priority_id": 2, "type_id": 4},
                        {"title": "Verify new user onboarding recommendations", "priority_id": 1, "type_id": 4},
                        {"title": "Verify 'Because You Watched' row accuracy", "priority_id": 2, "type_id": 4},
                    ]
                }
            ]
        },
        "Live Sports & Events": {
            "sections": [
                {
                    "name": "NFL Streaming",
                    "cases": [
                        {"title": "Verify NFL game stream starts at scheduled time", "priority_id": 1, "type_id": 4},
                        {"title": "Verify multi-camera angle switching during NFL game", "priority_id": 2, "type_id": 4},
                        {"title": "Verify NFL RedZone channel integration", "priority_id": 2, "type_id": 4},
                        {"title": "Verify NFL game DVR - pause and rewind live", "priority_id": 1, "type_id": 4},
                    ]
                },
                {
                    "name": "UEFA Champions League",
                    "cases": [
                        {"title": "Verify UCL match stream low-latency mode", "priority_id": 1, "type_id": 4},
                        {"title": "Verify UCL multi-match view (split screen)", "priority_id": 2, "type_id": 4},
                        {"title": "Verify UCL geo-restriction enforcement", "priority_id": 1, "type_id": 4},
                    ]
                }
            ]
        },
        "RCA Pipeline - AI Generated": {
            "sections": [
                {
                    "name": "Auth Service Incidents",
                    "cases": [
                        {"title": "RCA: Verify auth service handles null session tokens gracefully", "priority_id": 1, "type_id": 1, "refs": "PROD-001"},
                        {"title": "RCA: Verify auth service returns 401 not 500 for expired tokens", "priority_id": 1, "type_id": 1, "refs": "PROD-001"},
                    ]
                },
                {
                    "name": "CDN Incidents",
                    "cases": [
                        {"title": "RCA: Verify CDN failover to secondary edge on primary saturation", "priority_id": 1, "type_id": 1, "refs": "PROD-002"},
                        {"title": "RCA: Verify adaptive bitrate downgrades before buffer underrun", "priority_id": 1, "type_id": 1, "refs": "PROD-002"},
                    ]
                }
            ]
        }
    }

    total_cases = 0
    for suite_name, suite_id in created_suites.items():
        suite_config = test_cases_by_suite.get(suite_name, {})
        for section_data in suite_config.get("sections", []):
            sec_resp = _tr("POST", f"add_section/{project_id}", {
                "suite_id": suite_id,
                "name": section_data["name"]
            })
            if sec_resp.status_code not in (200, 201):
                print(f"  Section FAILED: {section_data['name']}")
                continue
            section_id = sec_resp.json()["id"]

            for case in section_data.get("cases", []):
                payload = {
                    "title": case["title"],
                    "priority_id": case.get("priority_id", 2),
                    "type_id": case.get("type_id", 4),
                    "custom_automation_type": random.choice([0, 1, 1, 2]),
                }
                if case.get("refs"):
                    payload["refs"] = case["refs"]

                c_resp = _tr("POST", f"add_case/{section_id}", payload)
                if c_resp.status_code in (200, 201):
                    total_cases += 1
                time.sleep(0.15)

    print(f"\n  Total suites: {len(created_suites)}")
    print(f"  Total test cases: {total_cases}")


# =============================================================================
# 3. NEW RELIC -- Create dashboards, alert policies & conditions via NerdGraph
# =============================================================================
def _nerdgraph(query, variables=None):
    """Execute a NerdGraph mutation/query."""
    headers = {"Api-Key": NR_API_KEY, "Content-Type": "application/json"}
    body = {"query": query}
    if variables:
        body["variables"] = variables
    resp = requests.post("https://api.newrelic.com/graphql", headers=headers, json=body, timeout=15)
    return resp


def seed_newrelic():
    banner("SEEDING NEW RELIC")
    if not NR_API_KEY:
        print("  SKIP: No NEWRELIC_API_KEY configured")
        return

    acct = int(NR_ACCOUNT_ID)
    total_created = 0

    # --- 1. Create Alert Policy ---
    policy_mutation = """
    mutation($accountId: Int!, $name: String!) {
      alertsPolicyCreate(accountId: $accountId, policy: {
        name: $name,
        incidentPreference: PER_CONDITION
      }) {
        id
        name
      }
    }
    """
    policies = [
        "Paramount+ Streaming - P1 Critical",
        "Paramount+ Auth & Payments",
        "Paramount+ CDN & Content Delivery",
        "Paramount+ Live Sports & Events",
    ]
    created_policy_ids = []
    for pname in policies:
        r = _nerdgraph(policy_mutation, {"accountId": acct, "name": pname})
        if r.status_code == 200:
            data = r.json().get("data", {})
            pol = data.get("alertsPolicyCreate")
            if pol and pol.get("id"):
                created_policy_ids.append(pol["id"])
                print(f"  Alert Policy: {pol['id']} - {pol['name']}")
                total_created += 1
            else:
                errs = r.json().get("errors", [])
                print(f"  Policy '{pname}': {errs[0].get('message','unknown')[:100] if errs else 'created (no id)'}")
        else:
            print(f"  Policy FAILED ({r.status_code}): {r.text[:150]}")
        time.sleep(0.3)

    # --- 2. Create NRQL Alert Conditions ---
    condition_mutation = """
    mutation CreateCondition($accountId: Int!, $policyId: ID!, $condition: AlertsNrqlConditionStaticInput!) {
      alertsNrqlConditionStaticCreate(accountId: $accountId, policyId: $policyId, condition: $condition) {
        id
        name
      }
    }
    """
    conditions = [
        {
            "enabled": True,
            "name": "Auth Service Error Rate > 5%",
            "nrql": {"query": "SELECT percentage(count(*), WHERE httpResponseCode >= 500) FROM Transaction WHERE appName = 'auth-service'"},
            "terms": [{"threshold": 5, "thresholdOccurrences": "AT_LEAST_ONCE", "thresholdDuration": 300, "operator": "ABOVE", "priority": "CRITICAL"}],
            "expiration": {"closeViolationsOnExpiration": True, "expirationDuration": 900, "openViolationOnExpiration": False},
            "signal": {"aggregationWindow": 60, "aggregationMethod": "EVENT_FLOW", "aggregationDelay": 120},
            "violationTimeLimitSeconds": 86400,
        },
        {
            "enabled": True,
            "name": "Streaming Latency p99 > 3s",
            "nrql": {"query": "SELECT percentile(duration, 99) FROM Transaction WHERE appName = 'streaming-service'"},
            "terms": [{"threshold": 3, "thresholdOccurrences": "AT_LEAST_ONCE", "thresholdDuration": 300, "operator": "ABOVE", "priority": "CRITICAL"}],
            "expiration": {"closeViolationsOnExpiration": True, "expirationDuration": 900, "openViolationOnExpiration": False},
            "signal": {"aggregationWindow": 60, "aggregationMethod": "EVENT_FLOW", "aggregationDelay": 120},
            "violationTimeLimitSeconds": 86400,
        },
        {
            "enabled": True,
            "name": "Payment Failures > 2%",
            "nrql": {"query": "SELECT percentage(count(*), WHERE error IS TRUE) FROM Transaction WHERE appName = 'payment-service'"},
            "terms": [{"threshold": 2, "thresholdOccurrences": "AT_LEAST_ONCE", "thresholdDuration": 300, "operator": "ABOVE", "priority": "CRITICAL"}],
            "expiration": {"closeViolationsOnExpiration": True, "expirationDuration": 900, "openViolationOnExpiration": False},
            "signal": {"aggregationWindow": 60, "aggregationMethod": "EVENT_FLOW", "aggregationDelay": 120},
            "violationTimeLimitSeconds": 86400,
        },
        {
            "enabled": True,
            "name": "CDN Buffering Ratio > 3%",
            "nrql": {"query": "SELECT average(bufferingRatio) FROM PageView WHERE appName LIKE 'paramount%25'"},
            "terms": [{"threshold": 3, "thresholdOccurrences": "AT_LEAST_ONCE", "thresholdDuration": 300, "operator": "ABOVE", "priority": "CRITICAL"}],
            "expiration": {"closeViolationsOnExpiration": True, "expirationDuration": 900, "openViolationOnExpiration": False},
            "signal": {"aggregationWindow": 60, "aggregationMethod": "EVENT_FLOW", "aggregationDelay": 120},
            "violationTimeLimitSeconds": 86400,
        },
        {
            "enabled": True,
            "name": "Content Catalog 5xx Errors",
            "nrql": {"query": "SELECT count(*) FROM Transaction WHERE appName = 'content-catalog' AND httpResponseCode >= 500"},
            "terms": [{"threshold": 50, "thresholdOccurrences": "AT_LEAST_ONCE", "thresholdDuration": 300, "operator": "ABOVE", "priority": "CRITICAL"}],
            "expiration": {"closeViolationsOnExpiration": True, "expirationDuration": 900, "openViolationOnExpiration": False},
            "signal": {"aggregationWindow": 60, "aggregationMethod": "EVENT_FLOW", "aggregationDelay": 120},
            "violationTimeLimitSeconds": 86400,
        },
        {
            "enabled": True,
            "name": "Live Sports Stream Delay > 30s",
            "nrql": {"query": "SELECT max(streamDelay) FROM Transaction WHERE appName = 'live-sports-service'"},
            "terms": [{"threshold": 30, "thresholdOccurrences": "AT_LEAST_ONCE", "thresholdDuration": 300, "operator": "ABOVE", "priority": "CRITICAL"}],
            "expiration": {"closeViolationsOnExpiration": True, "expirationDuration": 900, "openViolationOnExpiration": False},
            "signal": {"aggregationWindow": 60, "aggregationMethod": "EVENT_FLOW", "aggregationDelay": 120},
            "violationTimeLimitSeconds": 86400,
        },
    ]

    for i, cond in enumerate(conditions):
        pid = created_policy_ids[i % len(created_policy_ids)] if created_policy_ids else None
        if not pid:
            print(f"  Condition SKIP (no policy): {cond['name']}")
            continue
        r = _nerdgraph(condition_mutation, {
            "accountId": acct,
            "policyId": pid,
            "condition": cond,
        })
        if r.status_code == 200:
            data = r.json().get("data", {})
            cc = data.get("alertsNrqlConditionStaticCreate")
            if cc and cc.get("id"):
                print(f"  Alert Condition: {cc['id']} - {cc['name']}")
                total_created += 1
            else:
                errs = r.json().get("errors", [])
                print(f"  Condition '{cond['name']}': {errs[0].get('message','unknown')[:120] if errs else 'ok'}")
        else:
            print(f"  Condition FAILED ({r.status_code}): {r.text[:150]}")
        time.sleep(0.3)

    # --- 3. Create Dashboards via inline mutation (no variables for DashboardInput) ---
    def create_dashboard(name, pages_json):
        mutation = """
        mutation {
          dashboardCreate(accountId: %d, dashboard: %s) {
            entityResult { guid name }
            errors { description type }
          }
        }
        """ % (acct, pages_json)
        return _nerdgraph(mutation)

    def widget(title, viz, col, row, w, h, nrql):
        return '{title: "%s", visualization: {id: "%s"}, layout: {column: %d, row: %d, width: %d, height: %d}, rawConfiguration: {nrqlQueries: [{accountIds: [%d], query: "%s"}]}}' % (
            title, viz, col, row, w, h, acct, nrql.replace('"', '\\"')
        )

    dash1 = """{
        name: "Paramount+ Production Health",
        permissions: PUBLIC_READ_WRITE,
        pages: [
            {
                name: "Service Overview",
                widgets: [
                    %s,
                    %s,
                    %s,
                    %s
                ]
            },
            {
                name: "Streaming Quality",
                widgets: [
                    %s,
                    %s
                ]
            },
            {
                name: "Incidents & RCA",
                widgets: [
                    %s,
                    %s
                ]
            }
        ]
    }""" % (
        widget("Error Rate by Service", "viz.line", 1, 1, 6, 3,
               "SELECT percentage(count(*), WHERE httpResponseCode >= 500) FROM Transaction FACET appName TIMESERIES AUTO SINCE 1 day ago"),
        widget("P99 Latency by Service", "viz.line", 7, 1, 6, 3,
               "SELECT percentile(duration, 99) FROM Transaction FACET appName TIMESERIES AUTO SINCE 1 day ago"),
        widget("Throughput (RPM)", "viz.area", 1, 4, 4, 3,
               "SELECT rate(count(*), 1 minute) FROM Transaction FACET appName TIMESERIES AUTO SINCE 1 day ago"),
        widget("Top Errors", "viz.table", 5, 4, 8, 3,
               "SELECT count(*) FROM TransactionError FACET error.message, appName SINCE 1 day ago LIMIT 20"),
        widget("Buffering Ratio Trend", "viz.line", 1, 1, 6, 3,
               "SELECT average(bufferingRatio) FROM PageView TIMESERIES AUTO SINCE 1 day ago"),
        widget("Concurrent Streams", "viz.billboard", 7, 1, 6, 3,
               "SELECT max(concurrentStreams) as Peak, average(concurrentStreams) as Average FROM Transaction SINCE 1 hour ago"),
        widget("Open Incidents", "viz.table", 1, 1, 12, 3,
               "SELECT count(*) FROM NrAiIncident WHERE event = 'open' FACET conditionName, policyName SINCE 7 days ago"),
        widget("MTTR Trend (hours)", "viz.line", 1, 4, 6, 3,
               "SELECT average(durationSeconds)/3600 as 'MTTR hrs' FROM NrAiIncident WHERE event = 'close' TIMESERIES 1 day SINCE 30 days ago"),
    )

    r = create_dashboard("Paramount+ Production Health", dash1)
    if r.status_code == 200:
        data = r.json().get("data") or {}
        result = data.get("dashboardCreate") or {}
        entity = result.get("entityResult")
        errs = result.get("errors") or r.json().get("errors") or []
        if entity:
            print(f"  Dashboard: {entity.get('guid','?')[:40]}... - {entity.get('name')}")
            total_created += 1
        elif errs:
            msg = errs[0].get("description", errs[0].get("message", "unknown"))
            print(f"  Dashboard 1: {str(msg)[:150]}")
        else:
            print(f"  Dashboard 1: response - {json.dumps(r.json())[:200]}")
    else:
        print(f"  Dashboard 1 FAILED ({r.status_code}): {r.text[:200]}")

    # --- 4. RCA Pipeline dashboard ---
    dash2 = """{
        name: "RCA Pipeline - Incident Analysis",
        permissions: PUBLIC_READ_WRITE,
        pages: [{
            name: "RCA Overview",
            widgets: [
                %s,
                %s
            ]
        }]
    }""" % (
        widget("Recent Incidents by Service", "viz.bar", 1, 1, 6, 3,
               "SELECT count(*) FROM NrAiIncident FACET conditionName SINCE 30 days ago LIMIT 15"),
        widget("Incident Timeline", "viz.line", 7, 1, 6, 3,
               "SELECT count(*) FROM NrAiIncident FACET priority TIMESERIES 1 day SINCE 30 days ago"),
    )
    r2 = create_dashboard("RCA Pipeline", dash2)
    if r2.status_code == 200:
        data = r2.json().get("data") or {}
        result = data.get("dashboardCreate") or {}
        entity = result.get("entityResult")
        if entity:
            print(f"  Dashboard: {entity.get('guid','?')[:40]}... - {entity.get('name')}")
            total_created += 1
        else:
            errs = result.get("errors") or r2.json().get("errors") or []
            msg = errs[0].get("description", errs[0].get("message", "?"))[:120] if errs else "ok"
            print(f"  RCA Dashboard: {msg}")
    else:
        print(f"  RCA Dashboard FAILED: {r2.status_code}")

    print(f"\n  Total NR objects created: {total_created}")
    print(f"  Note: NerdGraph read API works (NRAK key). Ingest requires a License/Insert key.")


# =============================================================================
# 4. DATADOG -- Send Custom Metrics and Log Events
# =============================================================================
def seed_datadog():
    banner("SEEDING DATADOG")
    if not DD_API_KEY:
        print("  SKIP: No DD_API_KEY configured")
        return

    base_url = f"https://api.{DD_SITE}"
    headers = {
        "DD-API-KEY": DD_API_KEY,
        "Content-Type": "application/json"
    }

    now = int(time.time())
    services = [
        "auth-service", "streaming-service", "content-catalog",
        "payment-service", "recommendation-engine", "api-gateway"
    ]

    # Send custom metrics
    series = []
    for svc in services:
        for i in range(20):
            ts = now - (i * 60)
            is_incident = svc in ("auth-service", "streaming-service") and i < 5

            series.append({
                "metric": f"paramount.{svc}.error_rate",
                "type": "gauge",
                "points": [[ts, round(random.uniform(5.0, 15.0) if is_incident else random.uniform(0.01, 0.5), 3)]],
                "tags": [f"service:{svc}", "env:production", f"region:{random.choice(['us-east-1', 'us-west-2'])}"]
            })
            series.append({
                "metric": f"paramount.{svc}.latency_p99",
                "type": "gauge",
                "points": [[ts, random.randint(2000, 8000) if is_incident else random.randint(50, 300)]],
                "tags": [f"service:{svc}", "env:production"]
            })
            series.append({
                "metric": f"paramount.{svc}.throughput",
                "type": "gauge",
                "points": [[ts, random.randint(100, 5000)]],
                "tags": [f"service:{svc}", "env:production"]
            })

    # Send metrics in batches
    total_metrics = 0
    for i in range(0, len(series), 50):
        batch = series[i:i+50]
        resp = requests.post(
            f"{base_url}/api/v1/series",
            headers=headers,
            json={"series": batch},
            timeout=15
        )
        if resp.status_code in (200, 202):
            total_metrics += len(batch)
            print(f"  Metrics batch {i//50 + 1}: {len(batch)} series")
        else:
            print(f"  Metrics FAILED ({resp.status_code}): {resp.text[:200]}")
        time.sleep(0.3)

    # Send log entries
    log_url = f"https://http-intake.logs.{DD_SITE}/api/v2/logs"
    log_entries = []

    log_messages = [
        ("auth-service", "error", "NullPointerException in AuthTokenService.validateSession() - session token is null for user_id=u_84721"),
        ("auth-service", "error", "Failed to validate JWT: token expired 45 minutes ago, user_id=u_99102"),
        ("auth-service", "warn", "Rate limit exceeded for IP 203.0.113.42 - 150 login attempts in 60 seconds"),
        ("streaming-service", "error", "CDN origin returned 503 for segment: /hls/live/nfl-afc/1080p/seg_00847.ts"),
        ("streaming-service", "error", "Buffer underrun detected: rebuffering event for session s_847291 after 12.3s"),
        ("streaming-service", "warn", "Adaptive bitrate downgrade: 7200kbps -> 2100kbps for 34,000 sessions"),
        ("content-catalog", "error", "MongoDB primary failover detected - reads returning stale data from replica"),
        ("content-catalog", "error", "Empty catalog response for /api/v2/browse/home - 0 items returned"),
        ("payment-service", "error", "Stripe webhook timeout after 30000ms for subscription sub_1NPkR2KX8kQz"),
        ("payment-service", "warn", "Dead letter queue depth: 847 failed payment events pending retry"),
        ("drm-service", "error", "Widevine license server certificate mismatch - Roku 4K devices affected"),
        ("drm-service", "error", "DRM license acquisition failed: error_code=6007 for device_type=roku_ultra"),
        ("recommendation-engine", "warn", "Redis cache TTL misconfigured: 72h instead of 15min for user-profiles"),
        ("recommendation-engine", "error", "Stale recommendations served to 23,000 new users - cache not invalidated"),
        ("api-gateway", "error", "Upstream connection pool exhausted for auth-service: 0/500 available"),
        ("api-gateway", "warn", "Circuit breaker OPEN for payment-service after 5 consecutive failures"),
        ("notification-service", "warn", "Duplicate push notification detected for campaign_id=c_nfl_reminder"),
        ("search-service", "error", "Elasticsearch index contains 847 duplicate documents for content_type=show"),
        ("analytics-pipeline", "warn", "Kafka consumer lag: 2.25M events behind for topic paramount.playback.events"),
        ("transcoding-service", "warn", "Transcoding queue depth: 847 jobs waiting, estimated delay: 45 minutes"),
    ]

    for i, (svc, level, msg) in enumerate(log_messages):
        for j in range(3):
            log_entries.append({
                "ddsource": "paramount-mcp",
                "ddtags": f"service:{svc},env:production,version:2.1.0",
                "hostname": f"{svc}-prod-{random.randint(1,5)}",
                "message": f"{datetime.utcnow().isoformat()}Z {level.upper()} [{svc}] {msg}",
                "service": svc,
                "status": level,
            })

    # Send logs in batches
    total_logs = 0
    for i in range(0, len(log_entries), 20):
        batch = log_entries[i:i+20]
        resp = requests.post(log_url, headers=headers, json=batch, timeout=15)
        if resp.status_code in (200, 202):
            total_logs += len(batch)
            print(f"  Logs batch {i//20 + 1}: {len(batch)} entries")
        else:
            print(f"  Logs FAILED ({resp.status_code}): {resp.text[:200]}")
        time.sleep(0.3)

    # Create a Datadog event
    event_resp = requests.post(
        f"{base_url}/api/v1/events",
        headers=headers,
        json={
            "title": "Paramount+ Production Incident: Auth Service P1",
            "text": "Auth service returning 500 errors on login. Error rate: 12.5%. ~45,000 users affected. NullPointerException in AuthTokenService.validateSession().",
            "priority": "normal",
            "tags": ["service:auth-service", "env:production", "severity:P1", "team:platform"],
            "alert_type": "error",
            "source_type_name": "paramount-mcp"
        },
        timeout=15
    )
    if event_resp.status_code in (200, 202):
        print(f"  Event created: Auth Service P1 incident")

    print(f"\n  Total metrics: {total_metrics}")
    print(f"  Total logs: {total_logs}")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  PARAMOUNT+ TEST DATA SEEDER")
    print("  Pushing realistic data to Jira, TestRail, New Relic, Datadog")
    print("=" * 70)

    seed_jira()
    seed_testrail()
    seed_newrelic()
    seed_datadog()

    banner("SEEDING COMPLETE")
    print("  All platforms seeded with test data.")
    print("  Start the server to see data: python -m mcp.server")
    print()
