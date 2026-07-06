"use client";

import { useDraggable } from "@dnd-kit/core";
import type { Application } from "@/lib/api";
import { daysSince, isStale, relativeTime } from "@/lib/stats";

interface ApplicationCardProps {
  application: Application;
  onClick?: () => void;
}

/** A draggable card for one application (User Story 1/3). Status changes now
 * happen via drag-and-drop or the detail panel's one-tap transition buttons
 * (see ApplicationDetailPanel) — the required WCAG 2.1 AA non-drag
 * equivalent (FR-011a) — so this card carries no status control itself. */
export default function ApplicationCard({
  application,
  onClick,
}: ApplicationCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: application.id });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 10,
      }
    : undefined;

  const stale = isStale(application);

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className={`cursor-grab touch-none rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--padding-card)] shadow-[var(--shadow-sm)] transition-[border-color,box-shadow] duration-150 ease-out hover:border-[rgb(163_230_53_/_0.5)] hover:shadow-[var(--shadow-glow)] active:cursor-grabbing ${
        isDragging ? "opacity-40" : ""
      }`}
    >
      <div className="flex items-start gap-2">
        <p className="m-0 flex-1 text-sm leading-snug font-medium text-[color:var(--text-primary)]">
          {application.role}
        </p>
        {stale && (
          <span
            title={`No activity in ${daysSince(application.updated_at)} days`}
            className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-[var(--status-interviewing-dot)]"
          />
        )}
      </div>
      <p className="m-0 mt-0.5 text-sm text-[color:var(--text-secondary)]">
        {application.company}
      </p>
      <p
        className={`m-0 mt-2 text-xs ${
          stale
            ? "text-[color:var(--status-interviewing-text)]"
            : "text-[color:var(--text-tertiary)]"
        }`}
      >
        {stale
          ? `No activity in ${daysSince(application.updated_at)}d`
          : `Updated ${relativeTime(application.updated_at)}`}
      </p>
    </div>
  );
}
