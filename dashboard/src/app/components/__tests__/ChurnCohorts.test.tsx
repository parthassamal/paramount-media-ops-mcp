import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { ChurnCohorts } from "../ChurnCohorts";

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve([
          { summary: "P1 - Login SSO issue", severity: "critical" },
          { summary: "CDN latency spike", severity: "high" },
        ]),
    } as Response)
  ) as any;
});

describe("ChurnCohorts", () => {
  it("renders cohort title", async () => {
    render(<ChurnCohorts />);
    await waitFor(() => {
      expect(screen.getByText("Issue Risk Cohorts")).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error("fail"))) as any;
    render(<ChurnCohorts />);
    await waitFor(() => {
      expect(screen.getByText(/fail/i)).toBeInTheDocument();
    });
  });

  it("shows empty state", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response)
    ) as any;
    render(<ChurnCohorts />);
    await waitFor(() => {
      expect(screen.getByText(/No issues found/i)).toBeInTheDocument();
    });
  });
});
