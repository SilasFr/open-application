"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, type BaseResume, type TailoredCV } from "@/lib/api";
import ResumeUploadStep from "@/components/tailor/ResumeUploadStep";
import JobDescriptionStep from "@/components/tailor/JobDescriptionStep";
import ProgressNarrative from "@/components/tailor/ProgressNarrative";
import TailorResult from "@/components/tailor/TailorResult";

type Phase = "loading" | "resume" | "jd" | "working" | "result";

const STEP_LABELS = ["Base resume", "Job description", "Result"] as const;

function stepIndexForPhase(phase: Phase): number {
  if (phase === "resume") return 0;
  if (phase === "jd") return 1;
  return 2; // working or result both read as "on the way to / at" the result step
}

function StepIndicator({ phase }: { phase: Phase }) {
  const current = stepIndexForPhase(phase);
  return (
    <ol className="m-0 flex list-none items-center gap-2 p-0">
      {STEP_LABELS.map((label, index) => {
        const isDone = index < current || (index === current && phase === "result");
        const isCurrent = index === current && phase !== "result";
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className={`flex h-5 w-5 items-center justify-center rounded-[var(--radius-token-full)] text-[10px] ${
                isDone
                  ? "bg-[image:var(--fill-primary)] text-[color:var(--fill-primary-text)]"
                  : isCurrent
                    ? "border border-[var(--border-strong)] bg-[var(--badge-count-bg)] text-[color:var(--text-primary)]"
                    : "border border-[var(--border-default)] text-[color:var(--text-tertiary)]"
              }`}
            >
              {isDone ? "✓" : index + 1}
            </span>
            <span
              className={`text-xs ${
                isDone || isCurrent
                  ? "text-[color:var(--text-primary)]"
                  : "text-[color:var(--text-tertiary)]"
              }`}
            >
              {label}
            </span>
            {index < STEP_LABELS.length - 1 && (
              <span className="mx-1 h-px w-4 bg-[var(--border-default)]" />
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default function TailorPage() {
  const [phase, setPhase] = useState<Phase>("loading");
  const [savedResume, setSavedResume] = useState<BaseResume | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [tailored, setTailored] = useState<TailoredCV | null>(null);
  const [error, setError] = useState<string | null>(null);

  // FR-014 / SC-005: land directly on the job-description step when a base
  // resume is already saved for the user, instead of re-prompting for upload.
  useEffect(() => {
    let cancelled = false;
    api
      .getBaseResume()
      .then((resume) => {
        if (cancelled) return;
        setSavedResume(resume);
        setPhase(resume ? "jd" : "resume");
      })
      .catch(() => {
        if (!cancelled) setPhase("resume");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleTailorSubmit() {
    if (!jobDescription.trim()) return;
    setError(null);
    setPhase("working");
    try {
      const result = await api.tailorCV({ job_description: jobDescription });
      setTailored(result);
      setPhase("result");
    } catch (e) {
      // Edge case: JD submitted with no saved base resume (e.g. a race between
      // two tabs) — redirect back to the upload step. Keyed off the backend's
      // stable error code, not the message text.
      if (e instanceof ApiError && e.code === "base_resume_not_found") {
        setSavedResume(null);
        setPhase("resume");
        setError("Please upload your base resume to continue.");
        return;
      }
      setError(e instanceof Error ? e.message : "Failed to tailor resume.");
      setPhase("jd");
    }
  }

  async function handleRefine(instructions: string) {
    if (!tailored) return;
    setError(null);
    setPhase("working");
    try {
      const result = await api.tailorCV({
        job_description: jobDescription,
        refinement_instructions: instructions,
        previous_tailored_cv_id: tailored.id,
      });
      setTailored(result);
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to refine resume.");
      setPhase("result");
    }
  }

  function handleStartOver() {
    // FR-023: start over into a new job description while retaining the
    // saved base resume.
    setJobDescription("");
    setTailored(null);
    setError(null);
    setPhase("jd");
  }

  function handleAttached(applicationId: string) {
    setTailored((prev) =>
      prev ? { ...prev, application_id: applicationId } : prev,
    );
  }

  const showWizardChrome = phase !== "loading";

  return (
    <div className="relative min-h-screen bg-[image:var(--gradient-page)]">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-[image:var(--glow-accent)]"
      />
      <main className="relative mx-auto max-w-[80rem] px-6 py-12">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link
            href="/"
            className="text-sm text-[color:var(--text-secondary)] hover:underline"
          >
            ← Home
          </Link>
          {showWizardChrome && <StepIndicator phase={phase} />}
        </div>

        <h1 className="sr-only">Tailor my CV</h1>

        {error && (
          <p
            className="mt-4 text-sm text-[color:var(--text-error)]"
            role="alert"
          >
            {error}
          </p>
        )}

        <div className="mt-8">
          {phase === "loading" && (
            <p className="text-sm text-[color:var(--text-tertiary)]">Loading…</p>
          )}

          {phase === "resume" && (
            <ResumeUploadStep
              savedResume={savedResume}
              uploadResume={api.uploadBaseResume}
              removeResume={api.deleteBaseResume}
              onUploaded={(resume) => setSavedResume(resume)}
              onRemoved={() => setSavedResume(null)}
              onContinue={() => setPhase("jd")}
            />
          )}

          {phase === "jd" && savedResume && (
            <JobDescriptionStep
              savedResume={savedResume}
              jobDescription={jobDescription}
              onChangeJobDescription={setJobDescription}
              onManageResume={() => setPhase("resume")}
              onBack={() => setPhase("resume")}
              onSubmit={handleTailorSubmit}
            />
          )}

          {phase === "working" && <ProgressNarrative />}

          {phase === "result" && tailored && (
            <TailorResult
              tailored={tailored}
              onAttached={handleAttached}
              onRefine={handleRefine}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </main>
    </div>
  );
}
