"use client";

import { useEffect, useState } from "react";
import { api, type ApplicationContact } from "@/lib/api";

interface ContactsSectionProps {
  applicationId: string;
}

/** Associated contacts (recruiters, hiring managers, referrers) for an application. */
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
    <div className="mt-6">
      <h3 className="text-sm font-semibold">Contacts</h3>

      <form onSubmit={handleAdd} className="mt-2 flex flex-wrap gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          className="flex-1 rounded-lg border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
        />
        <input
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="Role"
          className="flex-1 rounded-lg border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
        />
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="flex-1 rounded-lg border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-transparent"
        />
        <button
          type="submit"
          className="rounded-lg bg-black px-3 py-1 text-sm text-white dark:bg-white dark:text-black"
        >
          Add Contact
        </button>
      </form>

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

      <div className="mt-3 space-y-2">
        {loading && <p className="text-xs text-gray-500">Loading…</p>}
        {!loading && contacts.length === 0 && (
          <p className="text-xs text-gray-500">No contacts yet.</p>
        )}
        {contacts.map((contact) => (
          <div
            key={contact.id}
            className="rounded-lg border border-gray-200 p-2 text-sm dark:border-gray-800"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{contact.name}</p>
                <p className="text-xs text-gray-500">
                  {[contact.role, contact.email, contact.phone]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                {contact.linkedin_url && (
                  <a
                    href={contact.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline"
                  >
                    LinkedIn
                  </a>
                )}
              </div>
              <div className="flex gap-2 text-xs">
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
                  className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs dark:border-gray-700 dark:bg-transparent"
                />
                <button
                  onClick={() => void handleSaveLinkedin(contact.id)}
                  className="text-xs font-medium hover:underline"
                >
                  Save
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
