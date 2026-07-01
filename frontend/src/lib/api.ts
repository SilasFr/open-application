/**
 * Thin client for the FastAPI backend.
 *
 * NOTE: the backend currently identifies the user via an `X-User-Id` header stub
 * (see backend/app/core/security.py). Once Supabase-JWT auth lands, replace this
 * with the access token: `Authorization: Bearer <token>`.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Temporary demo identity until real auth is wired in.
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000000";

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": DEMO_USER_ID,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
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
};
