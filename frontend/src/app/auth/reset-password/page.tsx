"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

function validatePassword(password: string): string | null {
  if (password.length < 8) return "Password must be at least 8 characters.";
  if (!/[a-zA-Z]/.test(password)) return "Password must contain at least one letter.";
  if (!/[0-9]/.test(password)) return "Password must contain at least one number.";
  return null;
}

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handlePasswordChange(value: string) {
    setPassword(value);
    if (passwordError) setPasswordError(validatePassword(value));
  }

  function handleConfirmChange(value: string) {
    setConfirm(value);
    if (confirmError) setConfirmError(value !== password ? "Passwords do not match." : null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const pwdError = validatePassword(password);
    if (pwdError) {
      setPasswordError(pwdError);
      return;
    }
    if (password !== confirm) {
      setConfirmError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({ password });
      if (error) throw error;
      router.push("/tracker");
      router.refresh();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Failed to update password. The link may have expired — request a new one.",
      );
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-sm px-6 py-20">
      <h1 className="text-3xl font-bold">Set new password</h1>
      <p className="mt-2 text-sm text-gray-500">
        Choose a password with at least 8 characters, one letter, and one number.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => handlePasswordChange(e.target.value)}
            placeholder="New password"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-700 dark:bg-transparent"
          />
          {passwordError && (
            <p className="mt-1 text-sm text-red-600">{passwordError}</p>
          )}
        </div>

        <div>
          <input
            type="password"
            required
            value={confirm}
            onChange={(e) => handleConfirmChange(e.target.value)}
            placeholder="Confirm new password"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-700 dark:bg-transparent"
          />
          {confirmError && (
            <p className="mt-1 text-sm text-red-600">{confirmError}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50 dark:bg-white dark:text-black"
        >
          {loading ? "Updating…" : "Update password"}
        </button>
      </form>

      {error && (
        <div className="mt-4">
          <p className="text-sm text-red-600">{error}</p>
          <Link
            href="/login"
            className="mt-2 block text-sm text-gray-500 hover:underline"
          >
            ← Request a new reset link
          </Link>
        </div>
      )}
    </main>
  );
}
