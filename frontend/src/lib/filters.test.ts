import { describe, expect, it } from "vitest";
import type { Application } from "@/lib/api";
import {
  DEFAULT_FILTER_STATE,
  filterApplications,
  matchesDateWindow,
  matchesFilters,
  matchesQuery,
  matchesStatus,
} from "@/lib/filters";

const NOW = new Date("2026-07-06T12:00:00Z");

function daysAgo(n: number): string {
  const d = new Date(NOW);
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

function app(overrides: Partial<Application>): Application {
  return {
    id: overrides.id ?? "1",
    company: "Acme Corp",
    role: "Frontend Engineer",
    status: "saved",
    job_description: null,
    created_at: daysAgo(1),
    updated_at: daysAgo(1),
    ...overrides,
  };
}

describe("matchesQuery", () => {
  it("matches case-insensitively on company", () => {
    expect(matchesQuery(app({ company: "Widgetco" }), "widget")).toBe(true);
  });

  it("matches case-insensitively on role", () => {
    expect(matchesQuery(app({ role: "Product Designer" }), "DESIGNER")).toBe(
      true,
    );
  });

  it("matches partial substrings", () => {
    expect(matchesQuery(app({ company: "DataInc" }), "ata")).toBe(true);
  });

  it("does not match unrelated text", () => {
    expect(matchesQuery(app({ company: "Acme", role: "Engineer" }), "zzz")).toBe(
      false,
    );
  });

  it("matches everything for an empty query", () => {
    expect(matchesQuery(app({}), "")).toBe(true);
    expect(matchesQuery(app({}), "   ")).toBe(true);
  });
});

describe("matchesStatus", () => {
  it("matches everything when 'all' is selected", () => {
    expect(matchesStatus(app({ status: "interviewing" }), "all")).toBe(true);
  });

  it("matches only the exact status", () => {
    expect(matchesStatus(app({ status: "interviewing" }), "interviewing")).toBe(
      true,
    );
    expect(matchesStatus(app({ status: "interviewing" }), "applied")).toBe(
      false,
    );
  });
});

describe("matchesDateWindow", () => {
  it("matches everything for 'any'", () => {
    expect(matchesDateWindow(app({ created_at: daysAgo(90) }), "any", NOW)).toBe(
      true,
    );
  });

  it("matches within the last 7 days", () => {
    expect(matchesDateWindow(app({ created_at: daysAgo(5) }), "7", NOW)).toBe(
      true,
    );
    expect(matchesDateWindow(app({ created_at: daysAgo(8) }), "7", NOW)).toBe(
      false,
    );
  });

  it("matches within the last 30 days", () => {
    expect(matchesDateWindow(app({ created_at: daysAgo(29) }), "30", NOW)).toBe(
      true,
    );
    expect(matchesDateWindow(app({ created_at: daysAgo(31) }), "30", NOW)).toBe(
      false,
    );
  });
});

describe("matchesFilters (composed)", () => {
  it("requires all active filters to match at once", () => {
    const candidate = app({
      company: "Acme Corp",
      role: "Backend Engineer",
      status: "applied",
      created_at: daysAgo(3),
    });
    expect(
      matchesFilters(
        candidate,
        { query: "acme", status: "applied", dateWindow: "7" },
        NOW,
      ),
    ).toBe(true);
    // Status filter mismatch alone should fail the whole thing.
    expect(
      matchesFilters(
        candidate,
        { query: "acme", status: "interviewing", dateWindow: "7" },
        NOW,
      ),
    ).toBe(false);
    // Date window mismatch alone should fail the whole thing.
    expect(
      matchesFilters(
        { ...candidate, created_at: daysAgo(20) },
        { query: "acme", status: "applied", dateWindow: "7" },
        NOW,
      ),
    ).toBe(false);
  });

  it("the default filter state matches everything", () => {
    expect(matchesFilters(app({}), DEFAULT_FILTER_STATE, NOW)).toBe(true);
  });
});

describe("filterApplications", () => {
  it("narrows a list down to only the matching applications", () => {
    const apps = [
      app({ id: "1", company: "Acme", status: "applied", created_at: daysAgo(2) }),
      app({ id: "2", company: "Widgetco", status: "saved", created_at: daysAgo(2) }),
      app({ id: "3", company: "Acme", status: "interviewing", created_at: daysAgo(40) }),
    ];
    const result = filterApplications(
      apps,
      { query: "acme", status: "all", dateWindow: "7" },
      NOW,
    );
    expect(result.map((a) => a.id)).toEqual(["1"]);
  });
});
