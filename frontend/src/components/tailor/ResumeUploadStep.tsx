"use client";

import { useRef, useState } from "react";
import type { BaseResume } from "@/lib/api";

const ACCEPTED_TYPES = new Set([
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const ACCEPTED_EXTENSIONS = [".pdf", ".docx"];
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

const primaryButtonCls =
  "inline-flex items-center justify-center rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-4 py-2 text-sm font-medium text-[color:var(--fill-primary-text)] shadow-[var(--shadow-glow)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50";

const textButtonCls =
  "border-none bg-transparent p-0 text-sm text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] hover:underline";

function isAcceptedFile(file: File): boolean {
  if (ACCEPTED_TYPES.has(file.type)) return true;
  const lower = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

interface ResumeUploadStepProps {
  savedResume: BaseResume | null;
  onUploaded: (resume: BaseResume) => void;
  onRemoved: () => void;
  onContinue: () => void;
  uploadResume: (file: File) => Promise<BaseResume>;
  removeResume: () => Promise<void>;
}

/** Step 1 of the tailor wizard (User Story 6): upload/replace/remove the
 * persisted base resume. Lands here only when no resume is saved yet, or the
 * user explicitly chooses to replace/manage it. */
export default function ResumeUploadStep({
  savedResume,
  onUploaded,
  onRemoved,
  onContinue,
  uploadResume,
  removeResume,
}: ResumeUploadStepProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    if (!isAcceptedFile(file)) {
      setError("Unsupported file type — please upload a PDF or DOCX file.");
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError("File exceeds the 5 MB size limit.");
      return;
    }
    setIsUploading(true);
    try {
      const resume = await uploadResume(file);
      onUploaded(resume);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to upload resume.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleRemove() {
    setIsRemoving(true);
    setError(null);
    try {
      await removeResume();
      onRemoved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove resume.");
    } finally {
      setIsRemoving(false);
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void handleFile(file);
  }

  function openBrowse() {
    inputRef.current?.click();
  }

  return (
    <section className="mx-auto max-w-[36rem]">
      <h1 className="m-0 text-2xl font-semibold tracking-[var(--tracking-tight)] text-[color:var(--text-primary)]">
        Upload your base resume
      </h1>
      <p className="mt-2 text-sm text-[color:var(--text-secondary)]">
        Upload it once — we keep it saved so you can tailor for any job in
        seconds.
      </p>

      {!savedResume ? (
        <div
          role="button"
          tabIndex={0}
          aria-label="Drop your resume here, or click to browse"
          onClick={openBrowse}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openBrowse();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`mt-6 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-token-lg)] border-[1.5px] border-dashed px-6 py-12 text-center transition ${
            isDragOver
              ? "border-[rgb(163_230_53_/_0.6)] bg-[rgb(132_204_22_/_0.10)]"
              : "border-[var(--border-input)]"
          }`}
        >
          <p className="m-0 text-sm font-medium text-[color:var(--text-primary)]">
            {isUploading
              ? "Uploading…"
              : "Drop your resume here, or click to browse"}
          </p>
          <p className="m-0 text-xs text-[color:var(--text-tertiary)]">
            PDF or DOCX, up to 5 MB
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
              e.target.value = "";
            }}
          />
        </div>
      ) : (
        <div className="mt-6 flex items-center gap-3 rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-token-sm)] bg-[var(--badge-count-bg)] text-xs font-semibold text-[color:var(--badge-count-text)]">
            {savedResume.filename.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="m-0 truncate text-sm font-medium text-[color:var(--text-primary)]">
              {savedResume.filename}
            </p>
            <p className="m-0 text-xs text-[color:var(--text-tertiary)]">
              Saved to your account
            </p>
          </div>
          <div className="flex shrink-0 gap-3">
            <button
              type="button"
              className={textButtonCls}
              onClick={openBrowse}
              disabled={isUploading || isRemoving}
            >
              Replace
            </button>
            <button
              type="button"
              className={textButtonCls}
              onClick={handleRemove}
              disabled={isUploading || isRemoving}
            >
              {isRemoving ? "Removing…" : "Remove"}
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleFile(file);
                e.target.value = "";
              }}
            />
          </div>
        </div>
      )}

      {error && (
        <p className="mt-3 text-sm text-[color:var(--text-error)]" role="alert">
          {error}
        </p>
      )}

      <div className="mt-6 flex justify-end">
        <button
          type="button"
          className={primaryButtonCls}
          disabled={!savedResume}
          onClick={onContinue}
        >
          Continue
        </button>
      </div>
    </section>
  );
}
