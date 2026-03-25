import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { ParetoChart } from "../ParetoChart";

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve([
          { summary: "P1 - Critical auth issue", severity: "critical" },
          { summary: "P2 - CDN issue", severity: "high" },
          { summary: "Search slowness", severity: "medium" },
        ]),
    } as Response)
  ) as any;
});

describe("ParetoChart", () => {
  it("renders chart title", async () => {
    render(<ParetoChart />);
    await waitFor(() => {
      expect(screen.getByText("Pareto Analysis")).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false } as Response)) as any;
    render(<ParetoChart />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
    });
  });

  it("shows empty state when no issues", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response)
    ) as any;
    render(<ParetoChart />);
    await waitFor(() => {
      expect(screen.getByText(/No issues to analyze/i)).toBeInTheDocument();
    });
  });
});
