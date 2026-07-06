import { describe, expect, it } from "vitest";
import type { Application } from "@/lib/api";
import { computeStats, isStale, relativeTime } from "@/lib/stats";

const NOW = new Date("2026-07-06T12:00:00Z");

function daysAgo(n: number): string {
  const d = new Date(NOW);
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

function app(overrides: Partial<Application>): Application {
  return {
    id: overrides.id ?? "1",
    company: "Acme",
    role: "Engineer",
    status: "saved",
    job_description: null,
    created_at: daysAgo(10),
    updated_at: daysAgo(10),
    ...overrides,
  };
}

describe("computeStats", () => {
  it("returns 0% response rate when there are no applications beyond 'saved'", () => {
    const apps = [app({ id: "1", status: "saved" }), app({ id: "2", status: "saved" })];
    const stats = computeStats(apps, NOW);
    expect(stats.responseRate).toBe(0);
  });

  it("returns 0% response rate for an empty application list", () => {
    const stats = computeStats([], NOW);
    expect(stats.responseRate).toBe(0);
    expect(stats.active).toBe(0);
    expect(stats.interviewing).toBe(0);
    expect(stats.offers).toBe(0);
    expect(stats.needAttention).toBe(0);
  });

  it("computes active/interviewing/offers counts", () => {
    const apps = [
      app({ id: "1", status: "saved" }),
      app({ id: "2", status: "applied" }),
      app({ id: "3", status: "interviewing" }),
      app({ id: "4", status: "offer" }),
      app({ id: "5", status: "accepted" }),
      app({ id: "6", status: "rejected" }),
      app({ id: "7", status: "withdrawn" }),
    ];
    const stats = computeStats(apps, NOW);
    // active = saved, applied, interviewing, offer
    expect(stats.active).toBe(4);
    expect(stats.interviewing).toBe(1);
    // offers = offer + accepted
    expect(stats.offers).toBe(2);
  });

  it("computes response rate as round((interviewing+offer+accepted) / (total-saved) * 100)", () => {
    const apps = [
      app({ id: "1", status: "saved" }),
      app({ id: "2", status: "applied" }),
      app({ id: "3", status: "interviewing" }),
      app({ id: "4", status: "rejected" }),
    ];
    // beyondSaved = applied, interviewing, rejected = 3
    // respondedTo = interviewing = 1
    // rate = round(1/3 * 100) = 33
    const stats = computeStats(apps, NOW);
    expect(stats.responseRate).toBe(33);
  });

  describe("isStale", () => {
    it("is false for an active application updated within the last 7 days", () => {
      expect(
        isStale({ status: "applied", updated_at: daysAgo(6) }, NOW),
      ).toBe(false);
    });

    it("is true at exactly the 7-day boundary", () => {
      expect(
        isStale({ status: "applied", updated_at: daysAgo(7) }, NOW),
      ).toBe(true);
    });

    it("is true beyond the 7-day boundary", () => {
      expect(
        isStale({ status: "offer", updated_at: daysAgo(8) }, NOW),
      ).toBe(true);
    });

    it("is false for closed statuses regardless of age", () => {
      expect(
        isStale({ status: "rejected", updated_at: daysAgo(30) }, NOW),
      ).toBe(false);
      expect(
        isStale({ status: "accepted", updated_at: daysAgo(30) }, NOW),
      ).toBe(false);
      expect(
        isStale({ status: "withdrawn", updated_at: daysAgo(30) }, NOW),
      ).toBe(false);
    });
  });

  it("counts stale active applications under needAttention", () => {
    const apps = [
      app({ id: "1", status: "applied", updated_at: daysAgo(8) }),
      app({ id: "2", status: "saved", updated_at: daysAgo(1) }),
      app({ id: "3", status: "rejected", updated_at: daysAgo(30) }),
    ];
    const stats = computeStats(apps, NOW);
    expect(stats.needAttention).toBe(1);
  });
});

describe("relativeTime", () => {
  it("labels today, yesterday, and n days ago", () => {
    expect(relativeTime(daysAgo(0), NOW)).toBe("today");
    expect(relativeTime(daysAgo(1), NOW)).toBe("yesterday");
    expect(relativeTime(daysAgo(5), NOW)).toBe("5d ago");
  });
});
