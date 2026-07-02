"use client";

import { useEffect, useState } from "react";
import { api, type ApplicationTask } from "@/lib/api";

interface TasksSectionProps {
  applicationId: string;
}

/** Checklist tasks for an application: add, toggle completion, delete. */
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

  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold">Tasks</h3>

      <form onSubmit={handleAdd} className="mt-2 flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a task…"
          className="flex-1 rounded-lg border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
        />
        <button
          type="submit"
          className="rounded-lg bg-black px-3 py-1 text-sm text-white dark:bg-white dark:text-black"
        >
          Add
        </button>
      </form>

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

      <div className="mt-3 space-y-1">
        {loading && <p className="text-xs text-gray-500">Loading…</p>}
        {!loading && tasks.length === 0 && (
          <p className="text-xs text-gray-500">No tasks yet.</p>
        )}
        {tasks.map((task) => (
          <div
            key={task.id}
            className="flex items-center justify-between rounded-lg border border-gray-200 px-2 py-1 text-sm dark:border-gray-800"
          >
            <label className="flex flex-1 items-center gap-2">
              <input
                type="checkbox"
                checked={task.is_completed}
                onChange={() => void handleToggle(task)}
              />
              <span
                className={
                  task.is_completed ? "text-gray-400 line-through" : undefined
                }
              >
                {task.title}
              </span>
            </label>
            <button
              onClick={() => void handleDelete(task.id)}
              className="text-xs hover:underline"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
