import { describe, expect, it } from "vitest";
import type { ApplicationStatus } from "@/lib/api";
import { canTransition, columnToTargetStatus, legalTargetStatuses } from "@/lib/board";

// Mirrors backend/app/domain/value_objects.py's `_ALLOWED_TRANSITIONS`
// exactly. There's no way to import Python from a Vitest file, so this is a
// hardcoded parity fixture — if the backend's transition map ever changes,
// this test (and `frontend/src/lib/board.ts`) must be updated to match.
const BACKEND_ALLOWED_TRANSITIONS: Record<ApplicationStatus, ApplicationStatus[]> = {
  saved: ["applied", "withdrawn"],
  applied: ["interviewing", "rejected", "withdrawn"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: ["accepted", "rejected", "withdrawn"],
  accepted: [],
  rejected: [],
  withdrawn: [],
};

describe("board.ts transition rules parity with backend value_objects.py", () => {
  for (const [source, targets] of Object.entries(BACKEND_ALLOWED_TRANSITIONS)) {
    const from = source as ApplicationStatus;

    it(`legalTargetStatuses("${from}") matches the backend's allowed set`, () => {
      expect(new Set(legalTargetStatuses(from))).toEqual(new Set(targets));
    });

    it(`canTransition("${from}", ...) matches the backend for every status`, () => {
      const allStatuses: ApplicationStatus[] = [
        "saved",
        "applied",
        "interviewing",
        "offer",
        "accepted",
        "rejected",
        "withdrawn",
      ];
      for (const to of allStatuses) {
        expect(canTransition(from, to)).toBe(targets.includes(to));
      }
    });
  }
});

describe("columnToTargetStatus Closed-group mapping", () => {
  it("maps a drop on 'closed' to the first legal closed status, in accepted/rejected/withdrawn priority", () => {
    // offer can legally reach all three closed statuses -> accepted wins.
    expect(columnToTargetStatus("closed", "offer")).toBe("accepted");
    // applied can only legally reach rejected/withdrawn among closed statuses
    // (not accepted) -> rejected wins (it precedes withdrawn in priority).
    expect(columnToTargetStatus("closed", "applied")).toBe("rejected");
    // saved can only reach withdrawn among closed statuses.
    expect(columnToTargetStatus("closed", "saved")).toBe("withdrawn");
  });

  it("returns null when no closed status is legally reachable", () => {
    expect(columnToTargetStatus("closed", "accepted")).toBeNull();
    expect(columnToTargetStatus("closed", "rejected")).toBeNull();
    expect(columnToTargetStatus("closed", "withdrawn")).toBeNull();
  });

  it("maps a drop on a direct status column via canTransition", () => {
    expect(columnToTargetStatus("interviewing", "applied")).toBe(
      "interviewing",
    );
    expect(columnToTargetStatus("offer", "saved")).toBeNull();
  });
});
