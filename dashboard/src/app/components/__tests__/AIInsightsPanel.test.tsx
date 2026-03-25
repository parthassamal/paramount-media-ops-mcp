import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { AIInsightsPanel } from "../AIInsightsPanel";

const mockIssues = [
  { key: "PROD-1", summary: "P1 - Login SSO failure", severity: "critical", status: "Open", assignee: "Alice", url: "https://jira.example.com/PROD-1" },
  { key: "PROD-2", summary: "P2 - CDN buffer spike", severity: "high", status: "In Progress", assignee: "Bob", url: "https://jira.example.com/PROD-2" },
];

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(mockIssues) } as Response)
  ) as any;
});

describe("AIInsightsPanel", () => {
  it("renders insights from Jira issues", async () => {
    render(<AIInsightsPanel />);
    await waitFor(() => {
      expect(screen.getByText(/Authentication/)).toBeInTheDocument();
    });
  });

  it("shows priority counts", async () => {
    render(<AIInsightsPanel />);
    await waitFor(() => {
      expect(screen.getByText("Critical")).toBeInTheDocument();
      expect(screen.getByText("High Priority")).toBeInTheDocument();
    });
  });

  it("shows error state on failure", async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false } as Response)) as any;
    render(<AIInsightsPanel />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument();
    });
  });

  it("shows empty state when no issues", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response)
    ) as any;
    render(<AIInsightsPanel />);
    await waitFor(() => {
      expect(screen.getByText(/No production issues/i)).toBeInTheDocument();
    });
  });
});
