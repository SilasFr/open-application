"use client";

import type { DateWindow, FilterState, StatusFilter } from "@/lib/filters";

interface FilterToolbarProps {
  value: FilterState;
  onChange: (value: FilterState) => void;
}

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All statuses" },
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offer", label: "Offer" },
  { value: "accepted", label: "Accepted" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
];

const DATE_OPTIONS: { value: DateWindow; label: string }[] = [
  { value: "any", label: "Any time" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
];

const inputCls =
  "rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-3 py-2 text-sm text-[color:var(--text-primary)] outline-none";

/** Combinable search/status/date-added filters over the tracker board
 * (User Story 2): free-text company/role search, status equality, and a
 * date-added window, all client-side (FR-002, FR-003a). */
export default function FilterToolbar({ value, onChange }: FilterToolbarProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <div className="relative min-w-[200px] flex-[1_1_240px]">
        <span
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-[color:var(--text-tertiary)]"
        >
          ⌕
        </span>
        <input
          type="search"
          value={value.query}
          onChange={(e) => onChange({ ...value, query: e.target.value })}
          placeholder="Search by company or role…"
          aria-label="Search by company or role"
          className={`${inputCls} w-full pl-8`}
        />
      </div>
      <select
        value={value.status}
        onChange={(e) =>
          onChange({ ...value, status: e.target.value as StatusFilter })
        }
        aria-label="Filter by status"
        className={`${inputCls} cursor-pointer`}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <select
        value={value.dateWindow}
        onChange={(e) =>
          onChange({ ...value, dateWindow: e.target.value as DateWindow })
        }
        aria-label="Filter by date added"
        className={`${inputCls} cursor-pointer`}
      >
        {DATE_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
