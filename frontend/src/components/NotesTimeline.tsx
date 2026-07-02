"use client";

import { useEffect, useState } from "react";
import { api, type ApplicationNote } from "@/lib/api";

interface NotesTimelineProps {
  applicationId: string;
}

/** Reverse-chronological activity + notes timeline for one application. */
export default function NotesTimeline({ applicationId }: NotesTimelineProps) {
  const [notes, setNotes] = useState<ApplicationNote[]>([]);
  const [content, setContent] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setNotes(await api.listNotes(applicationId));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load timeline");
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
    if (!content.trim()) return;
    try {
      await api.createNote(applicationId, content);
      setContent("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add note");
    }
  }

  async function handleSaveEdit(noteId: string) {
    if (!editingContent.trim()) return;
    try {
      await api.updateNote(applicationId, noteId, editingContent);
      setEditingId(null);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update note");
    }
  }

  async function handleDelete(noteId: string) {
    try {
      await api.deleteNote(applicationId, noteId);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete note");
    }
  }

  return (
    <div>
      <h3 className="text-sm font-semibold">Timeline</h3>

      <form onSubmit={handleAdd} className="mt-2 flex gap-2">
        <input
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Add a note…"
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

      <div className="mt-3 space-y-2">
        {loading && <p className="text-xs text-gray-500">Loading…</p>}
        {!loading && notes.length === 0 && (
          <p className="text-xs text-gray-500">No activity yet.</p>
        )}
        {notes.map((note) => {
          const isEdited = note.updated_at > note.created_at;
          const isEditing = editingId === note.id;
          return (
            <div
              key={note.id}
              className="rounded-lg border border-gray-200 p-2 text-sm dark:border-gray-800"
            >
              {isEditing ? (
                <div className="flex gap-2">
                  <input
                    value={editingContent}
                    onChange={(e) => setEditingContent(e.target.value)}
                    className="flex-1 rounded border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
                  />
                  <button
                    onClick={() => void handleSaveEdit(note.id)}
                    className="text-xs font-medium hover:underline"
                  >
                    Save
                  </button>
                </div>
              ) : (
                <p>{note.content}</p>
              )}
              <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
                <span>
                  {note.type} · {new Date(note.created_at).toLocaleString()}
                  {isEdited && " · edited"}
                </span>
                {note.type === "note" && !isEditing && (
                  <span className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingId(note.id);
                        setEditingContent(note.content);
                      }}
                      className="hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => void handleDelete(note.id)}
                      className="hover:underline"
                    >
                      Delete
                    </button>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
