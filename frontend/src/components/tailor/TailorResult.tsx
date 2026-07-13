"use client";

import { useEffect, useRef, useState } from "react";
import { api, type Application, type TailoredCV } from "@/lib/api";

const primaryButtonCls =
  "inline-flex items-center justify-center rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-4 py-2 text-sm font-medium text-[color:var(--fill-primary-text)] shadow-[var(--shadow-glow)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50";

const ghostButtonCls =
  "inline-flex items-center justify-center rounded-[var(--radius-token-md)] border border-[var(--border-default)] bg-transparent px-4 py-2 text-sm font-medium text-[color:var(--text-primary)] transition hover:border-[var(--border-strong)] disabled:cursor-not-allowed disabled:opacity-50";

const textButtonCls =
  "border-none bg-transparent p-0 text-sm text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] hover:underline disabled:cursor-not-allowed disabled:opacity-50";

function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

interface TailorResultProps {
  tailored: TailoredCV;
  onAttached: (applicationId: string) => void;
  onRefine: (instructions: string) => void;
  onStartOver: () => void;
}

/** Result view for a tailored CV: the finished resume preview plus the action
 * bar (download, copy, save-to-application, refine, start over). */
export default function TailorResult({
  tailored,
  onAttached,
  onRefine,
  onStartOver,
}: TailorResultProps) {
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState<"pdf" | "docx" | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const [showSavePopover, setShowSavePopover] = useState(false);
  const [applications, setApplications] = useState<Application[] | null>(null);
  const [applicationsError, setApplicationsError] = useState<string | null>(
    null,
  );
  const [attaching, setAttaching] = useState(false);
  const [attachedApplicationId, setAttachedApplicationId] = useState<
    string | null
  >(tailored.application_id);
  const popoverRef = useRef<HTMLDivElement>(null);

  const [showRefineInput, setShowRefineInput] = useState(false);
  const [refineText, setRefineText] = useState("");

  // Reset local state derived from `tailored` when a new result arrives (e.g.
  // after a refine), per React's "adjust state during render" pattern.
  const [prevTailoredId, setPrevTailoredId] = useState(tailored.id);
  if (tailored.id !== prevTailoredId) {
    setPrevTailoredId(tailored.id);
    setAttachedApplicationId(tailored.application_id);
  }

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(timer);
  }, [copied]);

  useEffect(() => {
    if (!showSavePopover) return;
    function onClickOutside(e: MouseEvent) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node)
      ) {
        setShowSavePopover(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setShowSavePopover(false);
    }
    window.addEventListener("mousedown", onClickOutside);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("mousedown", onClickOutside);
      window.removeEventListener("keydown", onKey);
    };
  }, [showSavePopover]);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(tailored.content);
      setCopied(true);
    } catch {
      setDownloadError("Could not copy to clipboard.");
    }
  }

  async function handleDownload(format: "pdf" | "docx") {
    setDownloading(format);
    setDownloadError(null);
    try {
      const blob = await api.downloadTailoredCV(tailored.id, format);
      triggerBlobDownload(blob, `tailored-cv.${format}`);
    } catch (e) {
      setDownloadError(
        e instanceof Error ? e.message : "Failed to download file.",
      );
    } finally {
      setDownloading(null);
    }
  }

  async function openSavePopover() {
    setShowSavePopover(true);
    if (applications !== null) return;
    setApplicationsError(null);
    try {
      const list = await api.listApplications();
      setApplications(list);
    } catch (e) {
      setApplicationsError(
        e instanceof Error ? e.message : "Failed to load applications.",
      );
    }
  }

  async function handleAttach(applicationId: string) {
    setAttaching(true);
    setApplicationsError(null);
    try {
      await api.attachTailoredCV(tailored.id, applicationId);
      setAttachedApplicationId(applicationId);
      onAttached(applicationId);
      setShowSavePopover(false);
    } catch (e) {
      setApplicationsError(
        e instanceof Error ? e.message : "Failed to attach resume.",
      );
    } finally {
      setAttaching(false);
    }
  }

  function handleSubmitRefine() {
    if (!refineText.trim()) return;
    onRefine(refineText.trim());
  }

  const attachedApplication =
    applications?.find((a) => a.id === attachedApplicationId) ?? null;

  return (
    <section className="mx-auto max-w-[52rem]">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className={primaryButtonCls}
          disabled={downloading !== null}
          onClick={() => handleDownload("pdf")}
        >
          {downloading === "pdf" ? "Downloading…" : "Download PDF"}
        </button>
        <button
          type="button"
          className={ghostButtonCls}
          disabled={downloading !== null}
          onClick={() => handleDownload("docx")}
        >
          {downloading === "docx" ? "Downloading…" : "Download DOCX"}
        </button>
        <button type="button" className={ghostButtonCls} onClick={handleCopy}>
          {copied ? "Copied ✓" : "Copy text"}
        </button>

        <div className="relative">
          <button
            type="button"
            className={ghostButtonCls}
            onClick={() =>
              showSavePopover ? setShowSavePopover(false) : openSavePopover()
            }
          >
            {attachedApplication
              ? `Saved to ${attachedApplication.company} ✓`
              : "Save to application"}
          </button>
          {showSavePopover && (
            <div
              ref={popoverRef}
              role="dialog"
              aria-label="Save to application"
              className="absolute left-0 top-full z-10 mt-2 w-[240px] rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[image:var(--gradient-panel)] p-3 shadow-[var(--shadow-lg)] backdrop-blur-md"
            >
              {applications === null && !applicationsError && (
                <p className="m-0 text-xs text-[color:var(--text-tertiary)]">
                  Loading applications…
                </p>
              )}
              {applicationsError && (
                <p className="m-0 text-xs text-[color:var(--text-error)]">
                  {applicationsError}
                </p>
              )}
              {applications !== null && applications.length === 0 && (
                <p className="m-0 text-xs text-[color:var(--text-tertiary)]">
                  No tracked applications yet — add one from the Tracker
                  first.
                </p>
              )}
              {applications !== null && applications.length > 0 && (
                <ul className="m-0 flex max-h-[220px] flex-col gap-1 overflow-y-auto p-0">
                  {applications.map((application) => (
                    <li key={application.id} className="list-none">
                      <button
                        type="button"
                        disabled={attaching}
                        onClick={() => handleAttach(application.id)}
                        className="w-full rounded-[var(--radius-token-sm)] border-none bg-transparent px-2 py-1.5 text-left text-sm text-[color:var(--text-primary)] hover:bg-[var(--badge-count-bg)] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {application.role}{" "}
                        <span className="text-[color:var(--text-secondary)]">
                          · {application.company}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <button
          type="button"
          className={textButtonCls}
          onClick={() => setShowRefineInput((v) => !v)}
        >
          Refine…
        </button>
        <button type="button" className={textButtonCls} onClick={onStartOver}>
          Start over
        </button>
      </div>

      {downloadError && (
        <p className="mt-2 text-sm text-[color:var(--text-error)]" role="alert">
          {downloadError}
        </p>
      )}

      {showRefineInput && (
        <div className="mt-3 flex flex-wrap items-center gap-2 rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-3">
          <input
            type="text"
            value={refineText}
            onChange={(e) => setRefineText(e.target.value)}
            placeholder="e.g. Keep it to one page, emphasize leadership more…"
            className="min-w-[240px] flex-1 rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-3 py-2 text-sm text-[color:var(--text-primary)] outline-none"
          />
          <button
            type="button"
            className={primaryButtonCls}
            disabled={!refineText.trim()}
            onClick={handleSubmitRefine}
          >
            Regenerate
          </button>
        </div>
      )}

      <div className="mt-4 rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] px-6 py-7">
        {tailored.contact && (
          <div className="mb-5 border-b border-[var(--border-default)] pb-4 text-center">
            <h2 className="m-0 text-lg font-bold tracking-[var(--tracking-wide)] uppercase text-[color:var(--text-primary)]">
              {tailored.contact.name}
            </h2>
            <p className="mt-1 flex flex-wrap justify-center gap-x-2 gap-y-0.5 text-xs text-[color:var(--text-tertiary)]">
              {[
                tailored.contact.email,
                tailored.contact.phone,
                ...tailored.contact.links.map((l) => l.label),
              ]
                .filter(Boolean)
                .map((part, i, arr) => (
                  <span key={i}>
                    {part}
                    {i < arr.length - 1 && <span className="ml-2">·</span>}
                  </span>
                ))}
            </p>
            {tailored.contact.location && (
              <p className="m-0 text-xs text-[color:var(--text-tertiary)]">
                {tailored.contact.location}
              </p>
            )}
          </div>
        )}
        {tailored.sections.map((section) => (
          <div key={section.id} className="mb-4">
            <h3 className="m-0 border-b border-[var(--border-default)] pb-1 text-xs font-semibold tracking-[var(--tracking-wide)] uppercase text-[color:var(--text-tertiary)]">
              {section.heading}
            </h3>
            {section.bullets.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-sm leading-[var(--leading-relaxed)] text-[color:var(--text-primary)]">
                {section.bullets.map((bullet, i) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
            )}
            {section.entries.map((entry, i) => (
              <div key={i} className="mt-3">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="text-sm font-semibold text-[color:var(--text-primary)]">
                    {entry.title}
                    {entry.organization && (
                      <span className="font-normal text-[color:var(--text-secondary)]">
                        {" — "}
                        {entry.organization}
                      </span>
                    )}
                  </span>
                  {entry.date_range && (
                    <span className="shrink-0 text-xs text-[color:var(--text-tertiary)]">
                      {entry.date_range}
                    </span>
                  )}
                </div>
                {entry.context && (
                  <p className="m-0 text-xs italic text-[color:var(--text-tertiary)]">
                    {entry.context}
                  </p>
                )}
                {entry.bullets.length > 0 && (
                  <ul className="mt-1 list-disc pl-5 text-sm leading-[var(--leading-relaxed)] text-[color:var(--text-primary)]">
                    {entry.bullets.map((bullet, j) => (
                      <li key={j}>{bullet}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
