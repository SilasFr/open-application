"use client";

import { useState } from "react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import type { Application, ApplicationStatus } from "@/lib/api";
import { api } from "@/lib/api";
import {
  COLUMN_LABELS,
  COLUMN_ORDER,
  columnToTargetStatus,
  statusToColumn,
  type BoardColumnId,
} from "@/lib/board";
import ApplicationCard from "@/components/ApplicationCard";

interface KanbanBoardProps {
  applications: Application[];
  onCardClick?: (application: Application) => void;
  /** Called after a status change is confirmed by the API, so the parent can
   * keep its own source-of-truth list in sync (e.g. for search filtering). */
  onApplicationUpdated?: (application: Application) => void;
}

// Module-scope constant: useSensor/useSensors memoize by reference, so a
// fresh object literal on every render would defeat that memoization (and
// trip a React warning inside dnd-kit's internals).
const POINTER_ACTIVATION_CONSTRAINT = { distance: 8 };

const STATUS_DOT: Record<BoardColumnId, string> = {
  saved: "var(--status-saved-dot)",
  applied: "var(--status-applied-dot)",
  interviewing: "var(--status-interviewing-dot)",
  offer: "var(--status-offer-dot)",
  closed: "var(--status-withdrawn-dot)",
};

function Column({
  id,
  count,
  legal,
  dragging,
  children,
}: {
  id: BoardColumnId;
  count: number;
  legal: boolean;
  dragging: boolean;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  const highlight = isOver && legal;

  return (
    <div
      ref={setNodeRef}
      className="flex min-h-[280px] w-full flex-1 flex-col gap-2 rounded-[var(--radius-token-lg)] border p-3 transition-[background-color,border-color,opacity] duration-150 ease-out sm:min-w-[200px]"
      style={{
        borderColor: highlight
          ? "rgb(163 230 53 / 0.5)"
          : "var(--border-default)",
        background: highlight
          ? "rgb(132 204 22 / 0.10)"
          : "rgb(148 163 184 / 0.04)",
        opacity: dragging && !legal ? 0.45 : 1,
      }}
    >
      <div className="flex items-center justify-between px-1">
        <h2 className="m-0 flex items-center gap-2 text-xs font-semibold tracking-[var(--tracking-wide)] text-[color:var(--text-primary)] uppercase">
          <span
            className="inline-block h-[7px] w-[7px] rounded-full"
            style={{ background: STATUS_DOT[id] }}
          />
          {COLUMN_LABELS[id]}
        </h2>
        <span className="rounded-[var(--radius-token-full)] bg-[var(--badge-count-bg)] px-2 py-0.5 text-xs font-medium text-[color:var(--badge-count-text)]">
          {count}
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {count === 0 && (
          <p className="m-0 my-3 mx-1 text-xs text-[color:var(--text-tertiary)]">
            Nothing here yet.
          </p>
        )}
        {children}
      </div>
    </div>
  );
}

/** Kanban board over an application list: drag a card between columns
 * (validated server-side) or, for the WCAG 2.1 AA non-drag equivalent, use
 * the detail panel's one-tap transition buttons. */
export default function KanbanBoard({
  applications,
  onCardClick,
  onApplicationUpdated,
}: KanbanBoardProps) {
  // Local, optimistic view of statuses. Resynced whenever the parent passes a
  // new `applications` reference (e.g. after a create or full refresh). This
  // is React's documented pattern for resetting state from a prop change —
  // storing the previous prop in state (not a ref) keeps it compiler-safe.
  const [items, setItems] = useState(applications);
  const [error, setError] = useState<string | null>(null);
  const [prevApplications, setPrevApplications] = useState(applications);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  // Require a small movement before a drag activates, so a plain click (no
  // movement) still reaches the card's onClick instead of being captured as
  // a zero-distance drag.
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: POINTER_ACTIVATION_CONSTRAINT,
    }),
    // Keyboard-operable drag-and-drop (research.md #9, FR-011a): focus a
    // card, press Space/Enter to pick it up, arrow keys to move between
    // droppable columns, Space/Enter again to drop, Escape to cancel.
    useSensor(KeyboardSensor),
  );
  if (prevApplications !== applications) {
    setPrevApplications(applications);
    setItems(applications);
  }

  const byColumn = new Map<BoardColumnId, Application[]>(
    COLUMN_ORDER.map((id) => [id, []]),
  );
  for (const app of items) {
    byColumn.get(statusToColumn(app.status))!.push(app);
  }

  const draggingApplication = draggingId
    ? items.find((a) => a.id === draggingId)
    : undefined;

  async function moveTo(application: Application, target: ApplicationStatus) {
    const previous = application.status;
    setError(null);
    // Optimistic move.
    setItems((current) =>
      current.map((a) => (a.id === application.id ? { ...a, status: target } : a)),
    );
    try {
      const updated = await api.changeStatus(application.id, target);
      setItems((current) =>
        current.map((a) => (a.id === updated.id ? updated : a)),
      );
      onApplicationUpdated?.(updated);
    } catch (e) {
      // Revert on failure (e.g. 409 illegal transition).
      setItems((current) =>
        current.map((a) =>
          a.id === application.id ? { ...a, status: previous } : a,
        ),
      );
      setError(e instanceof Error ? e.message : "Failed to update status");
    }
  }

  function handleDragStart(event: DragStartEvent) {
    setError(null);
    setDraggingId(String(event.active.id));
  }

  function handleDragEnd(event: DragEndEvent) {
    setDraggingId(null);
    const { active, over } = event;
    if (!over) return;
    const application = items.find((a) => a.id === active.id);
    if (!application) return;
    const target = columnToTargetStatus(
      over.id as BoardColumnId,
      application.status,
    );
    if (!target) {
      setError("That move isn't allowed for this application's status.");
      return;
    }
    if (target === application.status) return;
    void moveTo(application, target);
  }

  function handleDragCancel() {
    setDraggingId(null);
  }

  return (
    <div>
      {error && (
        <p className="mb-3 text-sm text-[color:var(--text-error)]">{error}</p>
      )}
      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:overflow-x-auto sm:pb-2">
          {COLUMN_ORDER.map((columnId) => {
            const cards = byColumn.get(columnId)!;
            const legal =
              draggingApplication == null
                ? true
                : columnToTargetStatus(columnId, draggingApplication.status) !=
                  null;
            return (
              <Column
                key={columnId}
                id={columnId}
                count={cards.length}
                legal={legal}
                dragging={draggingApplication != null}
              >
                {cards.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    application={application}
                    onClick={() => onCardClick?.(application)}
                  />
                ))}
              </Column>
            );
          })}
        </div>
      </DndContext>
    </div>
  );
}
