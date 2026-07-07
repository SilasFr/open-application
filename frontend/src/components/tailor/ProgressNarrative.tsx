"use client";

import { useEffect, useState } from "react";

const STEPS = [
  "Reading job description…",
  "Extracting key requirements…",
  "Matching your experience…",
  "Rewriting for relevance…",
  "Finalizing your tailored resume…",
];

const STEP_DURATION_MS = 900;

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** The "working" phase (User Story 6 AC3): a centered checklist stepping
 * through the narrative while the real tailoring request is in flight. This
 * is decorative narrative, not a literal progress bar — the actual API call
 * is single-shot; the parent phase transitions away once it resolves. */
export default function ProgressNarrative() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    // Deliberately reading a browser-only API (matchMedia) after mount rather
    // than via a lazy useState initializer: this is server-rendered, so the
    // initializer would return false on the server and (possibly) true on the
    // client, causing a hydration mismatch. Starting at false and correcting
    // post-mount avoids that; the one-frame flash is acceptable for a
    // reduced-motion preference read.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setReducedMotion(prefersReducedMotion());
  }, []);

  useEffect(() => {
    // When reduced motion is preferred, skip the stepped reveal and render the
    // final state directly (see the isDone/isCurrent computation below) rather
    // than forcing activeIndex via setState here.
    if (reducedMotion) return;
    if (activeIndex >= STEPS.length - 1) return;
    const timer = setTimeout(() => {
      setActiveIndex((i) => Math.min(i + 1, STEPS.length - 1));
    }, STEP_DURATION_MS);
    return () => clearTimeout(timer);
  }, [activeIndex, reducedMotion]);

  return (
    <section
      role="status"
      aria-live="polite"
      className="mx-auto flex max-w-[26rem] flex-col gap-3 py-16"
    >
      {STEPS.map((step, index) => {
        const isDone = reducedMotion ? true : index < activeIndex;
        const isCurrent = reducedMotion ? false : index === activeIndex;
        return (
          <div key={step} className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-[var(--radius-token-full)] text-xs ${
                isDone
                  ? "bg-[image:var(--fill-primary)] text-[color:var(--fill-primary-text)]"
                  : isCurrent
                    ? `border border-[var(--border-strong)] bg-[var(--badge-count-bg)] ${
                        reducedMotion ? "" : "animate-pulse"
                      }`
                    : "border border-[var(--border-default)]"
              }`}
            >
              {isDone ? "✓" : ""}
            </span>
            <p
              className={`m-0 text-sm ${
                isDone || isCurrent
                  ? "text-[color:var(--text-primary)]"
                  : "text-[color:var(--text-tertiary)]"
              }`}
            >
              {step}
            </p>
          </div>
        );
      })}
    </section>
  );
}
