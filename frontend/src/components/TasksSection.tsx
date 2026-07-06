"use client";

import { useEffect, useState } from "react";
import { api, type ApplicationTask } from "@/lib/api";

interface TasksSectionProps {
  applicationId: string;
}

const inputCls =
  "flex-1 rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-2.5 py-1.5 text-sm text-[color:var(--text-primary)] outline-none";

/** Follow-up checklist for an application (User Story 4): add, toggle
 * completion, delete. The count pill shows open (not-yet-completed) tasks. */
export default function TasksSection({ applicationId }: TasksSectionProps) {
  const [tasks, setTasks] = useState<ApplicationTask[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setTasks(await api.listTasks(applicationId));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicationId]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      await api.createTask(applicationId, title);
      setTitle("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add task");
    }
  }

  async function handleToggle(task: ApplicationTask) {
    try {
      await api.toggleTask(applicationId, task.id, !task.is_completed);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update task");
    }
  }

  async function handleDelete(taskId: string) {
    try {
      await api.deleteTask(applicationId, taskId);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete task");
    }
  }

  const openCount = tasks.filter((t) => !t.is_completed).length;

  return (
    <section className="mt-6">
      <div className="mb-2 flex items-center gap-2">
        <h3 className="m-0 text-sm font-semibold text-[color:var(--text-primary)]">
          Tasks
        </h3>
        {openCount > 0 && (
          <span className="rounded-[var(--radius-token-full)] bg-[var(--badge-count-bg)] px-2 py-px text-xs font-medium text-[color:var(--badge-count-text)]">
            {openCount}
          </span>
        )}
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a task…"
          className={inputCls}
        />
        <button
          type="submit"
          className="rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-3.5 py-1.5 text-xs font-semibold text-[color:var(--fill-primary-text)]"
        >
          Add
        </button>
      </form>

      {error && (
        <p className="mt-2 text-xs text-[color:var(--text-error)]">{error}</p>
      )}

      <div className="mt-2.5 flex flex-col gap-1.5">
        {loading && (
          <p className="text-xs text-[color:var(--text-secondary)]">
            Loading…
          </p>
        )}
        {!loading && tasks.length === 0 && (
          <p className="text-xs text-[color:var(--text-secondary)]">
            No tasks yet.
          </p>
        )}
        {tasks.map((task) => (
          <div
            key={task.id}
            className="flex items-center justify-between gap-2 rounded-[var(--radius-token-md)] border border-[var(--border-default)] bg-[var(--surface-card)] px-2.5 py-2 text-sm"
          >
            <label className="flex flex-1 cursor-pointer items-center gap-2.5">
              <input
                type="checkbox"
                checked={task.is_completed}
                onChange={() => void handleToggle(task)}
                className="cursor-pointer accent-[#a3e635]"
              />
              <span
                className={
                  task.is_completed
                    ? "text-[color:var(--text-tertiary)] line-through"
                    : "text-[color:var(--text-primary)]"
                }
              >
                {task.title}
              </span>
            </label>
            <button
              onClick={() => void handleDelete(task.id)}
              className="flex-shrink-0 text-xs text-[color:var(--text-secondary)] hover:underline"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
