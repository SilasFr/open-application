"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function TailorPage() {
  const [cvText, setCvText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cvText.trim() || !jobDescription.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const tailored = await api.tailorCV({
        cv_text: cvText,
        job_description: jobDescription,
      });
      setResult(tailored.content);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to tailor CV");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <Link href="/" className="text-sm text-gray-500 hover:underline">
        ← Home
      </Link>
      <h1 className="mt-4 text-3xl font-bold">Tailor my CV</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Your CV</label>
          <textarea
            value={cvText}
            onChange={(e) => setCvText(e.target.value)}
            rows={8}
            placeholder="Paste your current CV…"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-700 dark:bg-transparent"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">
            Job description
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={8}
            placeholder="Paste the job description…"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-700 dark:bg-transparent"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50 dark:bg-white dark:text-black"
        >
          {loading ? "Tailoring…" : "Tailor CV"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {result && (
        <section className="mt-8">
          <h2 className="text-xl font-semibold">Tailored CV</h2>
          <pre className="mt-2 whitespace-pre-wrap rounded-xl border border-gray-200 p-4 text-sm dark:border-gray-800">
            {result}
          </pre>
        </section>
      )}
    </main>
  );
}
