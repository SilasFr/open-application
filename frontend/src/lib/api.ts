/**
 * Thin client for the FastAPI backend.
 *
 * Authenticates by sending the current Supabase session's access token as
 * `Authorization: Bearer <token>`; the backend verifies it (see
 * backend/app/core/security.py). Requests made while signed out have no token
 * and the backend responds 401.
 */

import { createClient } from "@/lib/supabase/client";
import { isSupabaseConfigured } from "@/lib/supabase/config";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  if (!isSupabaseConfigured) return {};
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "offer"
  | "accepted"
  | "rejected"
  | "withdrawn";

export interface Application {
  id: string;
  company: string;
  role: string;
  status: ApplicationStatus;
  job_description: string | null;
  created_at: string;
  updated_at: string;
}

export interface TailoredCV {
  id: string;
  source_cv_id: string | null;
  job_description: string;
  content: string;
  created_at: string;
}

export type NoteType = "note" | "activity" | "email" | "call" | "interview";

export interface ApplicationNote {
  id: string;
  application_id: string;
  type: NoteType;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationContact {
  id: string;
  application_id: string;
  name: string;
  role: string | null;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  notes: string | null;
  created_at: string;
}

export interface ContactInput {
  name: string;
  role?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  notes?: string;
}

export interface ApplicationTask {
  id: string;
  application_id: string;
  title: string;
  is_completed: boolean;
  due_date: string | null;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders()),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      throw new Error("Please sign in to continue.");
    }
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  listApplications: () => request<Application[]>("/api/v1/applications"),

  createApplication: (input: {
    company: string;
    role: string;
    job_description?: string;
  }) =>
    request<Application>("/api/v1/applications", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  changeStatus: (id: string, status: ApplicationStatus) =>
    request<Application>(`/api/v1/applications/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  tailorCV: (input: { cv_text: string; job_description: string }) =>
    request<TailoredCV>("/api/v1/cv/tailor", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  listNotes: (applicationId: string) =>
    request<ApplicationNote[]>(`/api/v1/applications/${applicationId}/notes`),

  createNote: (applicationId: string, content: string) =>
    request<ApplicationNote>(`/api/v1/applications/${applicationId}/notes`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  updateNote: (applicationId: string, noteId: string, content: string) =>
    request<ApplicationNote>(
      `/api/v1/applications/${applicationId}/notes/${noteId}`,
      { method: "PATCH", body: JSON.stringify({ content }) },
    ),

  deleteNote: (applicationId: string, noteId: string) =>
    request<void>(`/api/v1/applications/${applicationId}/notes/${noteId}`, {
      method: "DELETE",
    }),

  listContacts: (applicationId: string) =>
    request<ApplicationContact[]>(
      `/api/v1/applications/${applicationId}/contacts`,
    ),

  createContact: (applicationId: string, input: ContactInput) =>
    request<ApplicationContact>(
      `/api/v1/applications/${applicationId}/contacts`,
      { method: "POST", body: JSON.stringify(input) },
    ),

  updateContact: (
    applicationId: string,
    contactId: string,
    input: Partial<ContactInput>,
  ) =>
    request<ApplicationContact>(
      `/api/v1/applications/${applicationId}/contacts/${contactId}`,
      { method: "PATCH", body: JSON.stringify(input) },
    ),

  deleteContact: (applicationId: string, contactId: string) =>
    request<void>(
      `/api/v1/applications/${applicationId}/contacts/${contactId}`,
      { method: "DELETE" },
    ),

  listTasks: (applicationId: string) =>
    request<ApplicationTask[]>(`/api/v1/applications/${applicationId}/tasks`),

  createTask: (applicationId: string, title: string) =>
    request<ApplicationTask>(`/api/v1/applications/${applicationId}/tasks`, {
      method: "POST",
      body: JSON.stringify({ title }),
    }),

  toggleTask: (applicationId: string, taskId: string, isCompleted: boolean) =>
    request<ApplicationTask>(
      `/api/v1/applications/${applicationId}/tasks/${taskId}`,
      { method: "PATCH", body: JSON.stringify({ is_completed: isCompleted }) },
    ),

  deleteTask: (applicationId: string, taskId: string) =>
    request<void>(`/api/v1/applications/${applicationId}/tasks/${taskId}`, {
      method: "DELETE",
    }),
};
