"use client";

import { useEffect, useState } from "react";
import { api, type ApplicationNote, type NoteType } from "@/lib/api";
import { relativeTime } from "@/lib/stats";

interface NotesTimelineProps {
  applicationId: string;
}

const NOTE_TYPE_LABEL: Record<NoteType, string> = {
  note: "Note",
  activity: "Activity",
  interview: "Interview",
  call: "Call",
  email: "Email",
};

const inputCls =
  "flex-1 rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-2.5 py-1.5 text-sm text-[color:var(--text-primary)] outline-none";

/** Reverse-chronological activity + notes timeline for one application
 * (User Story 4). */
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

  // Newest first, regardless of the order the API returns them in.
  const newestFirst = [...notes].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <section className="mt-6">
      <div className="mb-2 flex items-center gap-2">
        <h3 className="m-0 text-sm font-semibold text-[color:var(--text-primary)]">
          Timeline
        </h3>
        {notes.length > 0 && (
          <span className="rounded-[var(--radius-token-full)] bg-[var(--badge-count-bg)] px-2 py-px text-xs font-medium text-[color:var(--badge-count-text)]">
            {notes.length}
          </span>
        )}
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Add a note…"
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

      <div className="mt-2.5 flex flex-col gap-2">
        {loading && (
          <p className="text-xs text-[color:var(--text-secondary)]">
            Loading…
          </p>
        )}
        {!loading && notes.length === 0 && (
          <p className="text-xs text-[color:var(--text-secondary)]">
            No activity yet.
          </p>
        )}
        {newestFirst.map((note) => {
          const isEdited = note.updated_at > note.created_at;
          const isEditing = editingId === note.id;
          return (
            <div
              key={note.id}
              className="rounded-[var(--radius-token-md)] border border-[var(--border-default)] bg-[var(--surface-card)] p-2.5 text-sm"
            >
              {isEditing ? (
                <div className="flex gap-2">
                  <input
                    value={editingContent}
                    onChange={(e) => setEditingContent(e.target.value)}
                    className={inputCls}
                  />
                  <button
                    onClick={() => void handleSaveEdit(note.id)}
                    className="text-xs font-medium text-[color:var(--text-primary)] hover:underline"
                  >
                    Save
                  </button>
                </div>
              ) : (
                <p className="m-0 leading-normal text-[color:var(--text-primary)]">
                  {note.content}
                </p>
              )}
              <div className="mt-1 flex items-center justify-between text-xs text-[color:var(--text-tertiary)]">
                <span>
                  {NOTE_TYPE_LABEL[note.type] ?? note.type} ·{" "}
                  {relativeTime(note.created_at)}
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
    </section>
  );
}
