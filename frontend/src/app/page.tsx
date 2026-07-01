import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <h1 className="text-4xl font-bold tracking-tight">Open Application</h1>
      <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
        Track every job application in one place, and tailor your CV to any job
        description with AI.
      </p>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        <Link
          href="/tracker"
          className="rounded-xl border border-gray-200 p-6 transition hover:border-gray-400 dark:border-gray-800"
        >
          <h2 className="text-xl font-semibold">Tracker →</h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            See the progress of all your applications across their lifecycle.
          </p>
        </Link>

        <Link
          href="/tailor"
          className="rounded-xl border border-gray-200 p-6 transition hover:border-gray-400 dark:border-gray-800"
        >
          <h2 className="text-xl font-semibold">Tailor my CV →</h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Paste a job description and get your CV tailored to it.
          </p>
        </Link>
      </div>
    </main>
  );
}
