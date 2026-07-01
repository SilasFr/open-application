"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Application, type ApplicationStatus } from "@/lib/api";

const STATUSES: ApplicationStatus[] = [
  "saved",
  "applied",
  "interviewing",
  "offer",
  "accepted",
  "rejected",
  "withdrawn",
];

export default function TrackerPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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

  async function handleStatus(id: string, status: ApplicationStatus) {
    try {
      await api.changeStatus(id, status);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update status");
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
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

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-8 space-y-3">
        {loading && <p className="text-gray-500">Loading…</p>}
        {!loading && applications.length === 0 && (
          <p className="text-gray-500">No applications yet. Add one above.</p>
        )}
        {applications.map((app) => (
          <div
            key={app.id}
            className="flex items-center justify-between rounded-xl border border-gray-200 p-4 dark:border-gray-800"
          >
            <div>
              <p className="font-medium">{app.role}</p>
              <p className="text-sm text-gray-500">{app.company}</p>
            </div>
            <select
              value={app.status}
              onChange={(e) =>
                handleStatus(app.id, e.target.value as ApplicationStatus)
              }
              className="rounded-lg border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </main>
  );
}
