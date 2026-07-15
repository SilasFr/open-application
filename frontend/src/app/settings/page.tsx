"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  type AIProviderName,
  type AISettings,
} from "@/lib/api";

const inputCls =
  "w-full rounded-[var(--radius-token-md)] border border-[var(--border-input)] bg-[var(--surface-input)] px-3 py-2 text-sm text-[color:var(--text-primary)] outline-none";

const primaryButtonCls =
  "inline-flex items-center justify-center rounded-[var(--radius-token-md)] bg-[image:var(--fill-primary)] px-4 py-2 text-sm font-medium text-[color:var(--fill-primary-text)] shadow-[var(--shadow-glow)] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50";

const textButtonCls =
  "border-none bg-transparent p-0 text-sm text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] hover:underline disabled:cursor-not-allowed disabled:opacity-50";

const PROVIDER_LABELS: Record<AIProviderName, string> = {
  anthropic: "Anthropic",
  gemini: "Gemini",
  openai_compatible: "OpenAI-compatible (self-hosted / hosted open model)",
};

const DEFAULT_MODEL_FOR_PROVIDER: Record<AIProviderName, string> = {
  anthropic: "claude-3-5-haiku-latest",
  gemini: "gemini-2.0-flash",
  openai_compatible: "",
};

type Phase = "loading" | "ready";

/** BYOK settings page: shows whether the user has their own AI provider key
 * configured, or is on the platform's shared free tier, and lets them save or
 * remove a key. Saving validates the key with a live provider call before
 * persisting it (see backend/app/services/ai_settings_service.py). */
export default function SettingsPage() {
  const [phase, setPhase] = useState<Phase>("loading");
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [provider, setProvider] = useState<AIProviderName>("anthropic");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState(DEFAULT_MODEL_FOR_PROVIDER.anthropic);
  const [baseUrl, setBaseUrl] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getAISettings()
      .then((current) => {
        if (cancelled) return;
        setSettings(current);
        setPhase("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load AI settings.");
        setPhase("ready");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function handleProviderChange(next: AIProviderName) {
    setProvider(next);
    setModel(DEFAULT_MODEL_FOR_PROVIDER[next]);
  }

  const canSubmit = apiKey.trim() !== "" && model.trim() !== "";

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setIsSaving(true);
    try {
      const saved = await api.saveAISettings({
        provider,
        api_key: apiKey.trim(),
        model: model.trim(),
        base_url: provider === "openai_compatible" ? baseUrl.trim() : null,
      });
      setSettings(saved);
      setApiKey("");
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Failed to save — your key may have been rejected.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemove() {
    setError(null);
    setIsRemoving(true);
    try {
      await api.deleteAISettings();
      setSettings(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove your key.");
    } finally {
      setIsRemoving(false);
    }
  }

  return (
    <div className="relative min-h-screen bg-[image:var(--gradient-page)]">
      <main className="relative mx-auto max-w-[36rem] px-6 py-12">
        <Link
          href="/"
          className="text-sm text-[color:var(--text-secondary)] hover:underline"
        >
          ← Home
        </Link>

        <h1 className="mt-4 text-2xl font-semibold tracking-[var(--tracking-tight)] text-[color:var(--text-primary)]">
          AI provider settings
        </h1>
        <p className="mt-2 text-sm text-[color:var(--text-secondary)]">
          Bring your own AI provider key for reliable, unrate-limited CV
          tailoring — or stick with the platform&apos;s shared free tier.
        </p>

        {phase === "loading" && (
          <p className="mt-8 text-sm text-[color:var(--text-tertiary)]">
            Loading…
          </p>
        )}

        {phase === "ready" && (
          <>
            <div className="mt-6 rounded-[var(--radius-token-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-4">
              {settings ? (
                <>
                  <p className="m-0 text-sm font-medium text-[color:var(--text-primary)]">
                    Using your own key · {PROVIDER_LABELS[settings.provider]}
                  </p>
                  <p className="m-0 mt-1 text-xs text-[color:var(--text-tertiary)]">
                    Model {settings.model} · Key ending in {settings.key_last4}
                  </p>
                  <div className="mt-3">
                    <button
                      type="button"
                      className={textButtonCls}
                      onClick={handleRemove}
                      disabled={isRemoving}
                    >
                      {isRemoving ? "Removing…" : "Remove and use the free tier"}
                    </button>
                  </div>
                </>
              ) : (
                <p className="m-0 text-sm text-[color:var(--text-primary)]">
                  Using the shared platform free tier — expect rate limits at
                  peak times.
                </p>
              )}
            </div>

            <form onSubmit={handleSave} className="mt-6 flex flex-col gap-4">
              <div>
                <label
                  htmlFor="ai-provider"
                  className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
                >
                  Provider
                </label>
                <select
                  id="ai-provider"
                  value={provider}
                  onChange={(e) =>
                    handleProviderChange(e.target.value as AIProviderName)
                  }
                  className={`${inputCls} cursor-pointer`}
                >
                  {Object.entries(PROVIDER_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="ai-api-key"
                  className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
                >
                  API key
                </label>
                <input
                  id="ai-api-key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-…"
                  autoComplete="off"
                  className={inputCls}
                />
              </div>

              <div>
                <label
                  htmlFor="ai-model"
                  className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
                >
                  Model
                </label>
                <input
                  id="ai-model"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className={inputCls}
                />
              </div>

              {provider === "openai_compatible" && (
                <div>
                  <label
                    htmlFor="ai-base-url"
                    className="mb-1 block text-sm font-medium text-[color:var(--text-primary)]"
                  >
                    Endpoint URL
                  </label>
                  <input
                    id="ai-base-url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="http://localhost:11434/v1"
                    className={inputCls}
                  />
                </div>
              )}

              {error && (
                <p
                  className="text-sm text-[color:var(--text-error)]"
                  role="alert"
                >
                  {error}
                </p>
              )}

              <div className="mt-1 flex justify-end">
                <button
                  type="submit"
                  disabled={!canSubmit || isSaving}
                  className={primaryButtonCls}
                >
                  {isSaving ? "Validating…" : "Save key"}
                </button>
              </div>
            </form>
          </>
        )}
      </main>
    </div>
  );
}
