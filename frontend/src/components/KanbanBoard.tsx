"use client";

import { useState } from "react";
import {
  DndContext,
  useDroppable,
  type DragEndEvent,
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

function Column({
  id,
  children,
  count,
}: {
  id: BoardColumnId;
  children: React.ReactNode;
  count: number;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-[200px] w-full flex-col gap-2 rounded-xl border p-3 sm:w-56 ${
        isOver
          ? "border-blue-400 bg-blue-50 dark:bg-blue-950/20"
          : "border-gray-200 dark:border-gray-800"
      }`}
    >
      <div className="flex items-center justify-between px-1">
        <h2 className="text-sm font-semibold">{COLUMN_LABELS[id]}</h2>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
          {count}
        </span>
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </div>
  );
}

/** Kanban board over an application list: drag a card between columns, or use
 * its status <select>, to change status (validated server-side). */
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

  function handleDragEnd(event: DragEndEvent) {
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

  return (
    <div>
      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
      <DndContext onDragEnd={handleDragEnd}>
        <div className="flex flex-col gap-3 sm:flex-row sm:overflow-x-auto sm:pb-2">
          {COLUMN_ORDER.map((columnId) => {
            const cards = byColumn.get(columnId)!;
            return (
              <Column key={columnId} id={columnId} count={cards.length}>
                {cards.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    application={application}
                    onClick={() => onCardClick?.(application)}
                    onStatusChange={(status) => void moveTo(application, status)}
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
