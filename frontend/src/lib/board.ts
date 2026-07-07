import type { ApplicationStatus } from "@/lib/api";

/** Kanban column ids. "closed" collapses the three terminal statuses. */
export type BoardColumnId =
  | "saved"
  | "applied"
  | "interviewing"
  | "offer"
  | "closed";

export const COLUMN_ORDER: BoardColumnId[] = [
  "saved",
  "applied",
  "interviewing",
  "offer",
  "closed",
];

export const COLUMN_LABELS: Record<BoardColumnId, string> = {
  saved: "Saved",
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  closed: "Closed",
};

/** Display labels for every concrete application status (not just columns) —
 * used by the status badge and one-tap transition pills in the detail panel. */
export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  saved: "Saved",
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  accepted: "Accepted",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

const CLOSED_STATUSES: ApplicationStatus[] = [
  "accepted",
  "rejected",
  "withdrawn",
];

/** Which board column an application's status belongs to. */
export function statusToColumn(status: ApplicationStatus): BoardColumnId {
  return CLOSED_STATUSES.includes(status)
    ? "closed"
    : (status as BoardColumnId);
}

// Mirrors the backend's allowed-transition rules
// (backend/app/domain/value_objects.py) so the UI can decide, client-side,
// whether a drag is legal and which concrete status a drop onto the
// collapsed "Closed" column should apply.
const ALLOWED_TRANSITIONS: Record<ApplicationStatus, ApplicationStatus[]> = {
  saved: ["applied", "withdrawn"],
  applied: ["interviewing", "rejected", "withdrawn"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: ["accepted", "rejected", "withdrawn"],
  accepted: [],
  rejected: [],
  withdrawn: [],
};

export function canTransition(
  from: ApplicationStatus,
  to: ApplicationStatus,
): boolean {
  return ALLOWED_TRANSITIONS[from].includes(to);
}

export function legalTargetStatuses(
  from: ApplicationStatus,
): ApplicationStatus[] {
  return ALLOWED_TRANSITIONS[from];
}

// Preference order used to pick one concrete terminal status when a card is
// dropped on the "Closed" column, which has no single corresponding status.
const CLOSED_DROP_PRIORITY: ApplicationStatus[] = [
  "accepted",
  "rejected",
  "withdrawn",
];

/**
 * The concrete status a drop on `column` should apply, given the card's
 * current status. Returns null if the column has no legal target status
 * (the drag should be rejected).
 */
export function columnToTargetStatus(
  column: BoardColumnId,
  currentStatus: ApplicationStatus,
): ApplicationStatus | null {
  if (column !== "closed") {
    const target = column as ApplicationStatus;
    return canTransition(currentStatus, target) ? target : null;
  }
  return (
    CLOSED_DROP_PRIORITY.find((candidate) =>
      canTransition(currentStatus, candidate),
    ) ?? null
  );
}
