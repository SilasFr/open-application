"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, type Application } from "@/lib/api";
import KanbanBoard from "@/components/KanbanBoard";
import SearchBar from "@/components/SearchBar";
import ApplicationDetailPanel from "@/components/ApplicationDetailPanel";

export default function TrackerPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Application | null>(null);

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

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!company.trim() || !role.trim()) return;
    try {
      await api.createApplication({ company, role });
      setCompany("");
      setRole("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create application");
    }
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return applications;
    return applications.filter(
      (a) =>
        a.company.toLowerCase().includes(q) || a.role.toLowerCase().includes(q),
    );
  }, [applications, query]);

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <Link href="/" className="text-sm text-gray-500 hover:underline">
        ← Home
      </Link>
      <h1 className="mt-4 text-3xl font-bold">Application Tracker</h1>

      <form onSubmit={handleCreate} className="mt-6 flex flex-wrap gap-2">
        <input
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Company"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-700 dark:bg-transparent"
        />
        <input
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="Role"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-700 dark:bg-transparent"
        />
        <button
          type="submit"
          className="rounded-lg bg-black px-4 py-2 text-white dark:bg-white dark:text-black"
        >
          Add
        </button>
      </form>

      <div className="mt-6">
        <SearchBar value={query} onChange={setQuery} />
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-6">
        {loading && <p className="text-gray-500">Loading…</p>}
        {!loading && applications.length === 0 && (
          <p className="text-gray-500">No applications yet. Add one above.</p>
        )}
        {!loading && applications.length > 0 && (
          <KanbanBoard
            applications={filtered}
            onCardClick={setSelected}
            onApplicationUpdated={(updated) =>
              setApplications((current) =>
                current.map((a) => (a.id === updated.id ? updated : a)),
              )
            }
          />
        )}
      </div>

      {selected && (
        <ApplicationDetailPanel
          application={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </main>
  );
}
