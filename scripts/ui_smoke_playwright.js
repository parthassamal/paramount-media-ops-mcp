#!/usr/bin/env node
const { chromium } = require("playwright");

async function run() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const results = [];

  function record(name, ok, note = "") {
    results.push({ name, ok, note });
  }

  async function safeStep(name, fn) {
    try {
      await fn();
      record(name, true);
    } catch (e) {
      record(name, false, String(e.message || e).slice(0, 240));
    }
  }

  await safeStep("open_app", async () => {
    await page.goto("http://localhost:5173", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.getByText("Paramount+", { exact: false }).first().waitFor({ timeout: 20000 });
  });

  await safeStep("login_google", async () => {
    await page.getByRole("button", { name: /Continue with Google/i }).click({ timeout: 20000 });
    await page.getByRole("heading", { name: /Dashboard/i }).waitFor({ timeout: 30000 });
  });

  const navChecks = [
    { nav: "Dashboard", title: /Dashboard/i },
    { nav: "AI Insights", title: /AI Insights/i },
    { nav: "Production Issues", title: /Production Issues/i },
    { nav: "Review Queue", title: /Human Review Queue/i },
    { nav: "Pipeline Status", title: /Pipeline Status/i },
    { nav: "RCA Artifacts", title: /RCA Artifacts/i },
    { nav: "Test Impact Analysis", title: /Test Impact Analysis/i },
    { nav: "Failure Triage", title: /Automated Failure Triage/i },
    { nav: "Suite Hygiene", title: /Suite Hygiene/i },
    { nav: "Deployment Risk", title: /Deployment Risk Score/i },
    { nav: "Pattern Detection", title: /Pattern Detection/i },
    { nav: "Alert-Driven Tests", title: /Alert-Driven Tests/i },
    { nav: "Test Effectiveness", title: /Test Effectiveness/i },
    { nav: "Integrations", title: /Integrations/i },
  ];

  for (const check of navChecks) {
    await safeStep(`nav_${check.nav}`, async () => {
      await page.getByRole("button", { name: new RegExp(check.nav, "i") }).first().click({ timeout: 15000 });
      await page.getByRole("heading", { name: check.title }).first().waitFor({ timeout: 20000 });
    });
  }

  // Key actions
  await safeStep("pipeline_status_actions", async () => {
    await page.getByRole("button", { name: /Pipeline Status/i }).first().click();
    await page.getByRole("button", { name: /^Refresh$/i }).click();
    const metrics = page.getByRole("button", { name: /^Metrics$/i }).first();
    if (await metrics.isVisible()) {
      await metrics.click();
    }
  });

  await safeStep("rca_artifacts_action", async () => {
    await page.getByRole("button", { name: /RCA Artifacts/i }).first().click();
    const openBtn = page.getByRole("button", { name: /^Open$/i }).first();
    if (await openBtn.isVisible()) {
      await openBtn.click();
    }
  });

  await safeStep("test_impact_action", async () => {
    await page.getByRole("button", { name: /Test Impact Analysis/i }).first().click();
    await page.getByPlaceholder(/auth-service, payment-api/i).fill("auth-service,payment-api");
    await page.getByRole("button", { name: /Analyze Impact/i }).click();
  });

  await safeStep("suite_hygiene_action", async () => {
    await page.getByRole("button", { name: /Suite Hygiene/i }).first().click();
    await page.getByRole("button", { name: /Run Hygiene Check/i }).click();
  });

  await safeStep("deployment_risk_action", async () => {
    await page.getByRole("button", { name: /Deployment Risk/i }).first().click();
    await page.getByPlaceholder(/auth-service, payment-api/i).fill("auth-service,payment-api");
    await page.getByRole("button", { name: /Calculate Risk/i }).click();
  });

  await safeStep("pattern_detection_action", async () => {
    await page.getByRole("button", { name: /Pattern Detection/i }).first().click();
    await page.getByRole("button", { name: /Detect Patterns/i }).click();
  });

  await safeStep("alert_tests_action", async () => {
    await page.getByRole("button", { name: /Alert-Driven Tests/i }).first().click();
    const btn = page.getByRole("button", { name: /Generate Tests/i }).first();
    if (await btn.isVisible()) {
      await btn.click();
    }
  });

  await safeStep("effectiveness_action", async () => {
    await page.getByRole("button", { name: /Test Effectiveness/i }).first().click();
    await page.getByRole("button", { name: /Calculate Scores/i }).click();
  });

  await safeStep("integrations_not_placeholder", async () => {
    await page.getByRole("button", { name: /Integrations/i }).first().click();
    await page.getByText(/Live integration health and configuration status/i).waitFor({ timeout: 15000 });
  });

  await safeStep("help_modal", async () => {
    await page.getByRole("button", { name: /Help & Docs/i }).first().click();
    await page.getByRole("heading", { name: /Help & Documentation/i }).waitFor({ timeout: 15000 });
  });

  const passed = results.filter((r) => r.ok).length;
  const failed = results.filter((r) => !r.ok);
  const summary = { total: results.length, passed, failed: failed.length, failedCases: failed, results };
  console.log(JSON.stringify(summary, null, 2));

  await browser.close();
  process.exit(failed.length > 0 ? 1 : 0);
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
