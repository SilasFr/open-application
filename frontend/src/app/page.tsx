import Link from "next/link";

const FEATURES = [
  {
    href: "/tracker",
    title: "Tracker",
    description:
      "See the progress of all your applications across their lifecycle, with a pipeline summary and stale-application alerts.",
  },
  {
    href: "/tailor",
    title: "Tailor my CV",
    description:
      "Upload a base resume once, paste a job description, and get a tailored version with explanations for every change.",
  },
] as const;

export default function Home() {
  return (
    <div className="relative min-h-screen bg-[image:var(--gradient-page)]">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-[image:var(--glow-accent)]"
      />
      <main className="relative mx-auto max-w-[48rem] px-6 pt-24 pb-20">
        <p className="m-0 text-xs font-semibold tracking-[var(--tracking-wide)] text-[color:var(--text-link)] uppercase">
          Open Application
        </p>
        <h1 className="mt-3 font-[var(--font-display)] text-5xl font-bold tracking-[var(--tracking-tight)] text-[color:var(--text-primary)]">
          Run your job search like a pipeline.
        </h1>
        <p className="mt-4 max-w-md text-lg text-[color:var(--text-secondary)]">
          Track every application in one place, and tailor your CV to any job
          description with AI.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {FEATURES.map((feature) => (
            <Link
              key={feature.href}
              href={feature.href}
              className="group rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-6 shadow-[var(--shadow-sm)] transition hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]"
            >
              <h2 className="m-0 font-[var(--font-display)] text-xl font-semibold text-[color:var(--text-primary)]">
                {feature.title}{" "}
                <span className="text-[color:var(--text-link)] transition group-hover:translate-x-0.5 inline-block">
                  →
                </span>
              </h2>
              <p className="mt-2 text-sm text-[color:var(--text-secondary)]">
                {feature.description}
              </p>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
