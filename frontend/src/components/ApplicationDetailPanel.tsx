"use client";

import { useEffect, useRef, useState } from "react";
import { api, type Application, type ApplicationStatus } from "@/lib/api";
import { legalTargetStatuses, STATUS_LABELS } from "@/lib/board";
import { daysSince, isStale, relativeTime } from "@/lib/stats";
import NotesTimeline from "@/components/NotesTimeline";
import ContactsSection from "@/components/ContactsSection";
import TasksSection from "@/components/TasksSection";

interface ApplicationDetailPanelProps {
  application: Application;
  onClose: () => void;
  /** Called after a one-tap status transition succeeds, so the parent (and
   * the board behind this panel) stay in sync. */
  onApplicationUpdated?: (application: Application) => void;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function StatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-[var(--radius-token-full)] px-2.5 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{
        background: `var(--status-${status}-bg)`,
        border: `1px solid var(--status-${status}-border)`,
        color: `var(--status-${status}-text)`,
      }}
    >
      <span
        className="h-1.5 w-1.5 flex-shrink-0 rounded-full"
        style={{ background: `var(--status-${status}-dot)` }}
      />
      {STATUS_LABELS[status]}
    </span>
  );
}

/** Slide-over with an application's status, one-tap transitions, timeline,
 * contacts, and tasks (User Story 4). Dismissible via close/overlay/Escape,
 * with focus trapped while open and returned to the board on close
 * (FR-011, FR-011a). */
export default function ApplicationDetailPanel({
  application,
  onClose,
  onApplicationUpdated,
}: ApplicationDetailPanelProps) {
  const [moveError, setMoveError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  // Focus trap + return-focus-on-close (WCAG 2.1 AA, FR-011a).
  useEffect(() => {
    previouslyFocused.current = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    const focusable = panel?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    focusable?.[0]?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panel) return;
      const nodes = panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      previouslyFocused.current?.focus();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function move(target: ApplicationStatus) {
    setMoveError(null);
    try {
      const updated = await api.changeStatus(application.id, target);
      onApplicationUpdated?.(updated);
    } catch (e) {
      setMoveError(
        e instanceof Error ? e.message : "Failed to update status",
      );
    }
  }

  const moves = legalTargetStatuses(application.status);
  const stale = isStale(application);

  return (
    <div className="fixed inset-0 z-20 flex justify-end">
      <button
        aria-label="Close"
        onClick={onClose}
        className="flex-1 cursor-pointer border-none bg-[var(--surface-overlay)]"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={`${application.role} details`}
        className="flex h-full w-full max-w-[30rem] flex-col overflow-y-auto border-l border-[var(--border-default)] bg-[image:var(--gradient-panel)] backdrop-blur-md"
      >
        {/* Sticky header */}
        <div className="sticky top-0 z-10 border-b border-[var(--border-default)] bg-[image:var(--gradient-panel)] px-5 py-4 backdrop-blur-md">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="m-0 text-lg font-semibold tracking-[var(--tracking-tight)] text-[color:var(--text-primary)]">
                {application.role}
              </h2>
              <p className="m-0 mt-0.5 text-sm text-[color:var(--text-secondary)]">
                {application.company} · added {relativeTime(application.created_at)}
              </p>
            </div>
            <button
              onClick={onClose}
              className="flex-shrink-0 border-none bg-transparent p-0 text-sm text-[color:var(--text-secondary)] hover:underline"
            >
              Close
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <StatusBadge status={application.status} />
            {moves.map((s) => (
              <button
                key={s}
                onClick={() => void move(s)}
                className="rounded-[var(--radius-token-full)] border border-[var(--border-input)] bg-transparent px-2.5 py-0.5 text-xs font-medium whitespace-nowrap text-[color:var(--text-secondary)] hover:bg-[var(--surface-raised)]"
              >
                → {STATUS_LABELS[s]}
              </button>
            ))}
          </div>

          {moveError && (
            <p className="mt-2 text-xs text-[color:var(--text-error)]">
              {moveError}
            </p>
          )}

          {stale && (
            <p className="mt-2.5 text-xs text-[color:var(--status-interviewing-text)]">
              No activity in {daysSince(application.updated_at)} days. Add a
              note or task to keep it moving.
            </p>
          )}
        </div>

        <div className="px-5 pb-6">
          <NotesTimeline applicationId={application.id} />
          <ContactsSection applicationId={application.id} />
          <TasksSection applicationId={application.id} />
        </div>
      </div>
    </div>
  );
}
