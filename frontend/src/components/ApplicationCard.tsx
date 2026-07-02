"use client";

import { useDraggable } from "@dnd-kit/core";
import type { Application, ApplicationStatus } from "@/lib/api";
import { legalTargetStatuses } from "@/lib/board";

interface ApplicationCardProps {
  application: Application;
  onStatusChange: (status: ApplicationStatus) => void;
  onClick?: () => void;
}

/** A draggable card for one application. Also offers a status <select> as a
 * non-drag control (FR-CRM-002: drag OR controls within the card) — the only
 * way to reach a specific terminal status (accepted/rejected/withdrawn). */
export default function ApplicationCard({
  application,
  onStatusChange,
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

  const options = legalTargetStatuses(application.status);

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`rounded-xl border border-gray-200 bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-black ${
        isDragging ? "opacity-50" : ""
      }`}
    >
      <div
        {...listeners}
        {...attributes}
        onClick={onClick}
        className="cursor-grab touch-none active:cursor-grabbing"
      >
        <p className="font-medium">{application.role}</p>
        <p className="text-sm text-gray-500">{application.company}</p>
      </div>
      {options.length > 0 && (
        <select
          value=""
          onChange={(e) => {
            if (e.target.value) {
              onStatusChange(e.target.value as ApplicationStatus);
            }
          }}
          onPointerDown={(e) => e.stopPropagation()}
          className="mt-2 w-full rounded-lg border border-gray-300 px-2 py-1 text-xs dark:border-gray-700 dark:bg-transparent"
        >
          <option value="">Move to…</option>
          {options.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
