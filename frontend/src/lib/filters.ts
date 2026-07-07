import type { Application, ApplicationStatus } from "@/lib/api";

/** How far back "date added" filtering can look. */
export type DateWindow = "any" | "7" | "30";

/** `status === "all"` is treated as "no status filter applied". */
export type StatusFilter = "all" | ApplicationStatus;

export interface FilterState {
  query: string;
  status: StatusFilter;
  dateWindow: DateWindow;
}

export const DEFAULT_FILTER_STATE: FilterState = {
  query: "",
  status: "all",
  dateWindow: "any",
};

/** Case-insensitive, partial match over company or role. */
export function matchesQuery(application: Application, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    application.company.toLowerCase().includes(q) ||
    application.role.toLowerCase().includes(q)
  );
}

/** `"all"` matches everything; otherwise an exact status match. */
export function matchesStatus(
  application: Application,
  status: StatusFilter,
): boolean {
  return status === "all" || application.status === status;
}

/** Whether `application.created_at` falls within the given date window,
 * relative to `now` (defaults to the current time). */
export function matchesDateWindow(
  application: Application,
  window: DateWindow,
  now: Date = new Date(),
): boolean {
  if (window === "any") return true;
  const days = window === "7" ? 7 : 30;
  const ageMs = now.getTime() - new Date(application.created_at).getTime();
  return ageMs <= days * 86_400_000;
}

/** Applies all three predicates together (FR-002). */
export function matchesFilters(
  application: Application,
  filters: FilterState,
  now: Date = new Date(),
): boolean {
  return (
    matchesQuery(application, filters.query) &&
    matchesStatus(application, filters.status) &&
    matchesDateWindow(application, filters.dateWindow, now)
  );
}

/** Filters a full application list down to those matching all active filters. */
export function filterApplications(
  applications: Application[],
  filters: FilterState,
  now: Date = new Date(),
): Application[] {
  return applications.filter((a) => matchesFilters(a, filters, now));
}
