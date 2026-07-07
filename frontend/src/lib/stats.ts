import type { Application, ApplicationStatus } from "@/lib/api";

/** Statuses considered "active" (still in play, not closed out). */
export const ACTIVE_STATUSES: ApplicationStatus[] = [
  "saved",
  "applied",
  "interviewing",
  "offer",
];

/** An application is stale once it's been this many days (or more) since its
 * last activity while still in an active status. */
export const STALE_DAYS = 7;

/** Milliseconds in a day, used to convert timestamp deltas into day counts. */
const MS_PER_DAY = 86_400_000;

/** Whole days elapsed between `iso` and `now` (defaults to the current time). */
export function daysSince(iso: string, now: Date = new Date()): number {
  return Math.floor((now.getTime() - new Date(iso).getTime()) / MS_PER_DAY);
}

/** Human-friendly relative time: "today" / "yesterday" / "{n}d ago". */
export function relativeTime(iso: string, now: Date = new Date()): string {
  const days = daysSince(iso, now);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  return `${days}d ago`;
}

/** True when `application` is in an active status and has had no activity
 * for `STALE_DAYS` or more (FR-008). */
export function isStale(
  application: Pick<Application, "status" | "updated_at">,
  now: Date = new Date(),
): boolean {
  return (
    ACTIVE_STATUSES.includes(application.status) &&
    daysSince(application.updated_at, now) >= STALE_DAYS
  );
}

export interface PipelineStats {
  active: number;
  interviewing: number;
  offers: number;
  /** 0-100, rounded. 0 when there's nothing to respond to yet (denominator 0). */
  responseRate: number;
  needAttention: number;
}

/** Computes the tracker's pipeline-summary stats (User Story 1). */
export function computeStats(
  applications: Application[],
  now: Date = new Date(),
): PipelineStats {
  const active = applications.filter((a) =>
    ACTIVE_STATUSES.includes(a.status),
  );
  // Everything except "saved" — the denominator for response rate.
  const beyondSaved = applications.filter((a) => a.status !== "saved");
  const respondedTo = applications.filter((a) =>
    (["interviewing", "offer", "accepted"] as ApplicationStatus[]).includes(
      a.status,
    ),
  );
  const offers = applications.filter((a) =>
    (["offer", "accepted"] as ApplicationStatus[]).includes(a.status),
  );
  const interviewing = applications.filter(
    (a) => a.status === "interviewing",
  );
  const needAttention = active.filter((a) => isStale(a, now));

  const responseRate = beyondSaved.length
    ? Math.round((respondedTo.length / beyondSaved.length) * 100)
    : 0;

  return {
    active: active.length,
    interviewing: interviewing.length,
    offers: offers.length,
    responseRate,
    needAttention: needAttention.length,
  };
}
