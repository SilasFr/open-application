"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, type Application } from "@/lib/api";
import KanbanBoard from "@/components/KanbanBoard";
import FilterToolbar from "@/components/FilterToolbar";
import StatsStrip from "@/components/StatsStrip";
import AddApplicationModal from "@/components/AddApplicationModal";
import ApplicationDetailPanel from "@/components/ApplicationDetailPanel";
import { DEFAULT_FILTER_STATE, filterApplications, type FilterState } from "@/lib/filters";

export default function TrackerPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTER_STATE);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);

  async function refresh() {
    try {
      setApplications(await api.listApplications());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load applications");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Load applications from the API on mount. State is only set after an await
    // inside refresh(), so this is not a synchronous cascading render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, []);

  function handleApplicationUpdated(updated: Application) {
    setApplications((current) =>
      current.map((a) => (a.id === updated.id ? updated : a)),
    );
  }

  async function handleAdd(input: {
    company: string;
    role: string;
    status: "saved" | "applied";
  }) {
    try {
      const created = await api.createApplication({
        company: input.company,
        role: input.role,
      });
      // The API always creates in "saved" status; move it if the user chose
      // "applied" as the starting status.
      const final =
        input.status === "applied"
          ? await api.changeStatus(created.id, "applied")
          : created;
      setApplications((current) => [...current, final]);
      setAddModalOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create application");
    }
  }

  const filtered = useMemo(
    () => filterApplications(applications, filters),
    [applications, filters],
  );

  const selected = selectedId
    ? (applications.find((a) => a.id === selectedId) ?? null)
    : null;

  return (
    <div className="relative min-h-screen bg-[image:var(--gradient-page)]">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-[image:var(--glow-accent)]"
      />
      <main className="relative mx-auto max-w-[80rem] px-6 pt-8 pb-12">
        <Link
          href="/"
          className="text-sm text-[color:var(--text-secondary)] hover:underline"
        >
          ← Home
        </Link>

        <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
          <h1 className="m-0 text-3xl font-bold text-[color:var(--text-primary)]">
            Application Tracker
          </h1>
          <button
            onClick={() => setAddModalOpen(true)}
            className="rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-4 py-2 text-sm font-semibold whitespace-nowrap text-[color:var(--fill-primary-text)] shadow-[var(--shadow-glow)]"
          >
            + Add application
          </button>
        </div>

        <div className="mt-6">
          <StatsStrip applications={applications} />
        </div>

        <div className="mt-4">
          <FilterToolbar value={filters} onChange={setFilters} />
        </div>

        {error && (
          <p className="mt-4 text-sm text-[color:var(--text-error)]">
            {error}
          </p>
        )}

        <div className="mt-5">
          {loading && (
            <p className="text-[color:var(--text-secondary)]">Loading…</p>
          )}
          {!loading && applications.length === 0 && (
            <p className="text-[color:var(--text-secondary)]">
              No applications yet. Use “+ Add application” to create one.
            </p>
          )}
          {!loading && applications.length > 0 && (
            <KanbanBoard
              applications={filtered}
              onCardClick={(a) => setSelectedId(a.id)}
              onApplicationUpdated={handleApplicationUpdated}
            />
          )}
        </div>

        {selected && (
          <ApplicationDetailPanel
            application={selected}
            onClose={() => setSelectedId(null)}
            onApplicationUpdated={handleApplicationUpdated}
          />
        )}

        {addModalOpen && (
          <AddApplicationModal
            onClose={() => setAddModalOpen(false)}
            onAdd={(input) => void handleAdd(input)}
          />
        )}
      </main>
    </div>
  );
}
