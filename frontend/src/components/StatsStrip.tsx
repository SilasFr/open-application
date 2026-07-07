import type { Application } from "@/lib/api";
import { computeStats } from "@/lib/stats";

interface StatsStripProps {
  applications: Application[];
}

/** Pipeline-health summary strip: Active / Interviewing / Offers / Response
 * rate / Need attention, computed from the current application set (User
 * Story 1). */
export default function StatsStrip({ applications }: StatsStripProps) {
  const stats = computeStats(applications);

  const cells = [
    { label: "Active", value: stats.active },
    { label: "Interviewing", value: stats.interviewing },
    { label: "Offers", value: stats.offers },
    { label: "Response rate", value: `${stats.responseRate}%` },
    {
      label: "Need attention",
      value: stats.needAttention,
      warn: stats.needAttention > 0,
    },
  ];

  return (
    <div className="flex overflow-hidden rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] shadow-[var(--shadow-sm)]">
      {cells.map((cell, i) => (
        <div
          key={cell.label}
          className={`min-w-0 flex-1 px-5 py-3 ${
            i === 0 ? "" : "border-l border-[var(--border-default)]"
          }`}
        >
          <p
            className={`m-0 font-[var(--font-display)] text-2xl leading-tight font-bold tracking-[var(--tracking-tight)] ${
              cell.warn
                ? "text-[color:var(--status-interviewing-text)]"
                : "text-[color:var(--text-primary)]"
            }`}
          >
            {cell.value}
          </p>
          <p className="mt-0.5 text-xs whitespace-nowrap text-[color:var(--text-secondary)]">
            {cell.label}
          </p>
        </div>
      ))}
    </div>
  );
}
