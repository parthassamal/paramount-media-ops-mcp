import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { ExecutiveKPIs } from "../ExecutiveKPIs";

const mockHealthResponse = {
  status: "healthy",
  integrations: {
    jira: { status: "live" },
    newrelic: { status: "live" },
    datadog: { status: "disabled" },
  },
};

const mockIssues = [
  { id: "1", key: "PROD-1", summary: "P1 - Auth failure", severity: "critical", status: "Open", created: "2025-12-01T10:00:00Z" },
  { id: "2", key: "PROD-2", summary: "P2 - CDN latency", severity: "high", status: "In Progress", created: "2025-12-02T10:00:00Z" },
  { id: "3", key: "PROD-3", summary: "Search index delay", severity: "medium", status: "Done", created: "2025-12-03T10:00:00Z" },
];

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = vi.fn((url: string) => {
    if (url.includes("/health")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockHealthResponse) } as Response);
    }
    if (url.includes("/api/jira/issues")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockIssues) } as Response);
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
  }) as any;
});

describe("ExecutiveKPIs", () => {
  it("renders loading state then shows KPI data", async () => {
    render(<ExecutiveKPIs />);
    await waitFor(() => {
      expect(screen.getByText(/Production Issues/i)).toBeInTheDocument();
    });
  });

  it("displays correct total issue count from API", async () => {
    render(<ExecutiveKPIs />);
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
    });
  });

  it("shows error state on fetch failure", async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error("Network error"))) as any;
    render(<ExecutiveKPIs />);
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });
});
