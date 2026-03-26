const { test, expect } = require("@playwright/test");

test.describe("UI smoke coverage", () => {
  test("full left-nav workflow", async ({ page }) => {
    await page.goto("http://localhost:5173", { waitUntil: "domcontentloaded" });
    await expect(page.getByText("Paramount+").first()).toBeVisible();

    await page.getByRole("button", { name: /Continue with Google/i }).click();
    await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible();

    const navs = [
      ["Dashboard", /Dashboard/i],
      ["AI Insights", /AI Insights/i],
      ["Production Issues", /Production Issues/i],
      ["Review Queue", /Human Review Queue/i],
      ["Pipeline Status", /Pipeline Status/i],
      ["RCA Artifacts", /RCA Artifacts/i],
      ["Test Impact Analysis", /Test Impact Analysis/i],
      ["Failure Triage", /Automated Failure Triage/i],
      ["Suite Hygiene", /Suite Hygiene/i],
      ["Deployment Risk", /Deployment Risk Score/i],
      ["Pattern Detection", /Pattern Detection/i],
      ["Alert-Driven Tests", /Alert-Driven Tests/i],
      ["Test Effectiveness", /Test Effectiveness/i],
      ["Integrations", /Integrations/i],
    ];

    for (const [navLabel, titleRegex] of navs) {
      await page.getByRole("button", { name: new RegExp(navLabel, "i") }).first().click();
      await expect(page.getByRole("heading", { name: titleRegex }).first()).toBeVisible();
    }

    await page.getByRole("button", { name: /Pipeline Status/i }).first().click();
    await page.getByRole("button", { name: /^Refresh$/i }).click();
    if (await page.getByRole("button", { name: /^Metrics$/i }).first().isVisible()) {
      await page.getByRole("button", { name: /^Metrics$/i }).first().click();
    }

    await page.getByRole("button", { name: /RCA Artifacts/i }).first().click();
    if (await page.getByRole("button", { name: /^Open$/i }).first().isVisible()) {
      await page.getByRole("button", { name: /^Open$/i }).first().click();
    }

    await page.getByRole("button", { name: /Test Impact Analysis/i }).first().click();
    await page.getByPlaceholder(/auth-service, payment-api/i).fill("auth-service,payment-api");
    await page.getByRole("button", { name: /Analyze Impact/i }).click();

    await page.getByRole("button", { name: /Suite Hygiene/i }).first().click();
    await page.getByRole("button", { name: /Run Hygiene Check/i }).click();

    await page.getByRole("button", { name: /Deployment Risk/i }).first().click();
    await page.getByPlaceholder(/auth-service, payment-api/i).fill("auth-service,payment-api");
    await page.getByRole("button", { name: /Calculate Risk/i }).click();

    await page.getByRole("button", { name: /Pattern Detection/i }).first().click();
    await page.getByRole("button", { name: /Detect Patterns/i }).click();

    await page.getByRole("button", { name: /Alert-Driven Tests/i }).first().click();
    if (await page.getByRole("button", { name: /Generate Tests/i }).first().isVisible()) {
      await page.getByRole("button", { name: /Generate Tests/i }).first().click();
    }

    await page.getByRole("button", { name: /Test Effectiveness/i }).first().click();
    await page.getByRole("button", { name: /Calculate Scores/i }).click();

    await page.getByRole("button", { name: /Integrations/i }).first().click();
    await expect(
      page.getByText(/Live integration health and configuration status/i)
    ).toBeVisible();

    await page.getByRole("button", { name: /Help & Docs/i }).first().click();
    await expect(page.getByRole("heading", { name: /Help & Documentation/i })).toBeVisible();
  });
});
