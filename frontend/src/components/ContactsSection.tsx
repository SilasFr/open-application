"use client";

import { useEffect, useState } from "react";
import { api, type ApplicationContact } from "@/lib/api";

interface ContactsSectionProps {
  applicationId: string;
}

const inputCls =
  "flex-1 rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-2.5 py-1.5 text-sm text-[color:var(--text-primary)] outline-none";

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/** Associated contacts (recruiters, hiring managers, referrers) for an
 * application (User Story 4). */
export default function ContactsSection({ applicationId }: ContactsSectionProps) {
  const [contacts, setContacts] = useState<ApplicationContact[]>([]);
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [email, setEmail] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingLinkedin, setEditingLinkedin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setContacts(await api.listContacts(applicationId));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load contacts");
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
    if (!name.trim()) return;
    try {
      await api.createContact(applicationId, {
        name,
        role: role || undefined,
        email: email || undefined,
      });
      setName("");
      setRole("");
      setEmail("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add contact");
    }
  }

  async function handleSaveLinkedin(contactId: string) {
    try {
      await api.updateContact(applicationId, contactId, {
        linkedin_url: editingLinkedin,
      });
      setEditingId(null);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update contact");
    }
  }

  async function handleDelete(contactId: string) {
    try {
      await api.deleteContact(applicationId, contactId);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete contact");
    }
  }

  return (
    <section className="mt-6">
      <div className="mb-2 flex items-center gap-2">
        <h3 className="m-0 text-sm font-semibold text-[color:var(--text-primary)]">
          Contacts
        </h3>
        {contacts.length > 0 && (
          <span className="rounded-[var(--radius-token-full)] bg-[var(--badge-count-bg)] px-2 py-px text-xs font-medium text-[color:var(--badge-count-text)]">
            {contacts.length}
          </span>
        )}
      </div>

      <form onSubmit={handleAdd} className="flex flex-wrap gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          className={inputCls}
        />
        <input
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="Role"
          className={inputCls}
        />
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className={inputCls}
        />
        <button
          type="submit"
          className="rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-3.5 py-1.5 text-xs font-semibold text-[color:var(--fill-primary-text)]"
        >
          Add contact
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
        {!loading && contacts.length === 0 && (
          <p className="text-xs text-[color:var(--text-secondary)]">
            No contacts yet.
          </p>
        )}
        {contacts.map((contact) => (
          <div
            key={contact.id}
            className="rounded-[var(--radius-token-md)] border border-[var(--border-default)] bg-[var(--surface-card)] p-2.5 text-sm"
          >
            <div className="flex items-center gap-2.5">
              <span
                aria-hidden="true"
                className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-[var(--radius-token-full)] bg-[var(--badge-count-bg)] text-xs font-semibold text-[color:var(--text-secondary)]"
              >
                {initials(contact.name)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="m-0 font-medium text-[color:var(--text-primary)]">
                  {contact.name}
                </p>
                <p className="m-0 mt-px text-xs text-[color:var(--text-secondary)]">
                  {[contact.role, contact.email].filter(Boolean).join(" · ")}
                </p>
              </div>
              {contact.linkedin_url && (
                <a
                  href={contact.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 text-xs text-[color:var(--text-link)] hover:underline"
                >
                  LinkedIn →
                </a>
              )}
              <div className="flex flex-shrink-0 gap-2 text-xs text-[color:var(--text-secondary)]">
                <button
                  onClick={() => {
                    setEditingId(contact.id);
                    setEditingLinkedin(contact.linkedin_url ?? "");
                  }}
                  className="hover:underline"
                >
                  Edit
                </button>
                <button
                  onClick={() => void handleDelete(contact.id)}
                  className="hover:underline"
                >
                  Delete
                </button>
              </div>
            </div>
            {editingId === contact.id && (
              <div className="mt-2 flex gap-2">
                <input
                  value={editingLinkedin}
                  onChange={(e) => setEditingLinkedin(e.target.value)}
                  placeholder="LinkedIn URL"
                  className={inputCls}
                />
                <button
                  onClick={() => void handleSaveLinkedin(contact.id)}
                  className="text-xs font-medium text-[color:var(--text-primary)] hover:underline"
                >
                  Save
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
