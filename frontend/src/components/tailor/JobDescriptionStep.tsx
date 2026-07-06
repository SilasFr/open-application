"use client";

import { useRef, useState } from "react";
import type { BaseResume } from "@/lib/api";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

const primaryButtonCls =
  "inline-flex items-center justify-center rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-4 py-2 text-sm font-medium text-[color:var(--fill-primary-text)] shadow-[var(--shadow-glow)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50";

const ghostButtonCls =
  "inline-flex items-center justify-center rounded-[var(--radius-token-md)] border border-[var(--border-default)] bg-transparent px-4 py-2 text-sm font-medium text-[color:var(--text-primary)] transition hover:border-[var(--border-strong)]";

const textButtonCls =
  "border-none bg-transparent p-0 text-sm text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] hover:underline";

interface JobDescriptionStepProps {
  savedResume: BaseResume;
  jobDescription: string;
  onChangeJobDescription: (value: string) => void;
  onManageResume: () => void;
  onBack: () => void;
  onSubmit: () => void;
}

/** Step 2 of the tailor wizard (User Story 6): paste or drop a job
 * description. The saved resume is shown as a read-only chip — replacing it
 * happens by returning to the resume step (`onManageResume`). */
export default function JobDescriptionStep({
  savedResume,
  jobDescription,
  onChangeJobDescription,
  onManageResume,
  onBack,
  onSubmit,
}: JobDescriptionStepProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function readFileAsText(file: File) {
    setError(null);
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError("File exceeds the 5 MB size limit.");
      return;
    }
    const isPlainText =
      file.type === "text/plain" || file.name.toLowerCase().endsWith(".txt");
    if (!isPlainText) {
      setError(
        "Unsupported file type for the job description — please paste the text or upload a .txt file.",
      );
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === "string" ? reader.result : "";
      onChangeJobDescription(text);
    };
    reader.onerror = () => setError("Failed to read the file.");
    reader.readAsText(file);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) readFileAsText(file);
  }

  const canSubmit = jobDescription.trim() !== "";

  return (
    <section className="mx-auto max-w-[36rem]">
      <h1 className="m-0 text-2xl font-semibold tracking-[var(--tracking-tight)] text-[color:var(--text-primary)]">
        Paste the job description
      </h1>

      <div className="mt-4 flex items-center gap-3 rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-token-sm)] bg-[var(--badge-count-bg)] text-xs font-semibold text-[color:var(--badge-count-text)]">
          {savedResume.filename.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC"}
        </div>
        <p className="m-0 min-w-0 flex-1 truncate text-sm text-[color:var(--text-secondary)]">
          {savedResume.filename}
        </p>
        <button type="button" className={textButtonCls} onClick={onManageResume}>
          Replace
        </button>
      </div>

      <textarea
        value={jobDescription}
        onChange={(e) => onChangeJobDescription(e.target.value)}
        rows={9}
        placeholder="Paste the job description…"
        className="mt-4 w-full rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-3 py-2 text-sm text-[color:var(--text-primary)] outline-none"
      />

      <div
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Drop a job description file here, or click to browse"
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`mt-3 cursor-pointer rounded-[var(--radius-token-lg)] border-[1.5px] border-dashed px-4 py-3 text-center text-xs transition ${
          isDragOver
            ? "border-[rgb(163_230_53_/_0.6)] bg-[rgb(132_204_22_/_0.10)] text-[color:var(--text-primary)]"
            : "border-[var(--border-input)] text-[color:var(--text-tertiary)]"
        }`}
      >
        Or drop a job description text file here
        <input
          ref={inputRef}
          type="file"
          accept=".txt,text/plain"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) readFileAsText(file);
            e.target.value = "";
          }}
        />
      </div>

      {error && (
        <p className="mt-3 text-sm text-[color:var(--text-error)]" role="alert">
          {error}
        </p>
      )}

      <div className="mt-6 flex justify-between">
        <button type="button" className={ghostButtonCls} onClick={onBack}>
          Back
        </button>
        <button
          type="button"
          className={primaryButtonCls}
          disabled={!canSubmit}
          onClick={onSubmit}
        >
          Tailor my resume
        </button>
      </div>
    </section>
  );
}
