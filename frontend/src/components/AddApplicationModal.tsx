"use client";

import { useEffect, useRef, useState } from "react";
import type { ApplicationStatus } from "@/lib/api";

interface AddApplicationModalProps {
  onClose: () => void;
  onAdd: (input: {
    company: string;
    role: string;
    status: Extract<ApplicationStatus, "saved" | "applied">;
  }) => void;
}

const inputCls =
  "w-full rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-3 py-2 text-sm text-[color:var(--text-primary)] outline-none";

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Add-application dialog (User Story 5): company/role/starting-status,
 * autofocus, disabled-until-valid submit, overlay-click/Cancel to close,
 * with focus trapped while open and returned to the trigger on close
 * (WCAG 2.1 AA, FR-011a). */
export default function AddApplicationModal({
  onClose,
  onAdd,
}: AddApplicationModalProps) {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [startingStatus, setStartingStatus] = useState<"saved" | "applied">(
    "saved",
  );
  const firstRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    previouslyFocused.current = document.activeElement as HTMLElement | null;
    firstRef.current?.focus();
    return () => {
      previouslyFocused.current?.focus();
    };
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const dialog = dialogRef.current;
      const nodes = dialog?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (!nodes || nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const canSubmit = company.trim() !== "" && role.trim() !== "";

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    onAdd({ company: company.trim(), role: role.trim(), status: startingStatus });
  }

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center p-6">
      <button
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-[var(--surface-overlay)]"
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Add application"
        className="relative w-full max-w-[26rem] rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[image:var(--gradient-panel)] p-6 shadow-[var(--shadow-lg)] backdrop-blur-md"
      >
        <div className="flex items-start justify-between">
          <h2 className="m-0 text-xl font-semibold tracking-[var(--tracking-tight)] text-[color:var(--text-primary)]">
            Add application
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="border-none bg-transparent p-0 text-sm text-[color:var(--text-secondary)] hover:underline"
          >
            ×
          </button>
        </div>
        <form onSubmit={submit} className="mt-5 flex flex-col gap-4">
          <div>
            <label
              htmlFor="add-app-company"
              className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
            >
              Company
            </label>
            <input
              id="add-app-company"
              ref={firstRef}
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company name…"
              className={inputCls}
            />
          </div>
          <div>
            <label
              htmlFor="add-app-role"
              className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
            >
              Role
            </label>
            <input
              id="add-app-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Role title…"
              className={inputCls}
            />
          </div>
          <div>
            <label
              htmlFor="add-app-status"
              className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
            >
              Starting status
            </label>
            <select
              id="add-app-status"
              value={startingStatus}
              onChange={(e) =>
                setStartingStatus(e.target.value as "saved" | "applied")
              }
              className={`${inputCls} cursor-pointer`}
            >
              <option value="saved">Saved</option>
              <option value="applied">Applied</option>
            </select>
          </div>
          <div className="mt-1 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center gap-2 rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-transparent px-4 py-2 text-sm font-medium text-[color:var(--text-primary)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="rounded-[var(--radius-token-md)] border border-transparent bg-[image:var(--fill-primary)] px-4 py-2 text-sm font-semibold text-[color:var(--fill-primary-text)] disabled:cursor-not-allowed disabled:opacity-50"
              style={canSubmit ? { boxShadow: "var(--shadow-glow)" } : undefined}
            >
              Add application
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
