import { useEffect, useRef, useState } from "react";
import { Eye, EyeOff, CheckCircle2, KeyRound } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/settings/settings-primitives";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import {
  deleteGeminiApiKey,
  getGeminiApiKeyForReveal,
  getGeminiKeyStatus,
  setGeminiApiKey,
  type GeminiKeyStatus,
} from "@/lib/api/ai-key";
import { clearAIKeyStatus, setAIKeyStatus } from "@/lib/auth/ai-key-storage";
import {
  isSupportedGeminiCredential,
  normalizeGeminiCredentialInput,
} from "@/features/ai-key/credential-validation";

const MODEL_NAME = "gemini-2.5-flash";

type GeminiApiKeyManagerProps = {
  compact?: boolean;
  hideWhenConfigured?: boolean;
  context?: "home" | "settings";
  onNotification?: (notification: GeminiApiKeyNotification) => void;
};

export type GeminiApiKeyNotification = {
  variant: "success" | "warning" | "error";
  title: string;
  description: string;
  autoDismissMs?: number;
};

export function GeminiApiKeyManager({
  compact = false,
  hideWhenConfigured = false,
  context = "settings",
  onNotification,
}: GeminiApiKeyManagerProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [status, setStatus] = useState<GeminiKeyStatus>({
    configured: false,
    masked_key: null,
    source: "none",
    model: MODEL_NAME,
    last_validated: null,
  });
  const [inputValue, setInputValue] = useState("");
  const [revealedSessionKey, setRevealedSessionKey] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [confirmRemoveOpen, setConfirmRemoveOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const showInlineFeedback = context !== "settings";

  const validateApiKeyFormat = (value: string): string | null => {
    if (!value) {
      return "Please enter your Gemini API key.";
    }

    if (!isSupportedGeminiCredential(value)) {
      return "This doesn't appear to be a supported Gemini credential.";
    }

    return null;
  };

  const formatLastValidated = (value: string | null): string => {
    if (!value) {
      return "Not available";
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return `${parsed.toISOString().replace("T", " ").replace(".000", "")}`;
  };

  const loadStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const next = await getGeminiKeyStatus();
      setStatus(next);
      setAIKeyStatus(next.configured, next.source);
      setRevealedSessionKey(null);
      setShowKey(false);

      if (next.configured && next.masked_key) {
        setInputValue(next.masked_key);
      } else {
        setInputValue("");
      }
    } catch {
      setError("Unable to load Gemini API key status.");
      clearAIKeyStatus();
      setStatus({
        configured: false,
        masked_key: null,
        source: "none",
        model: MODEL_NAME,
        last_validated: null,
      });
      setInputValue("");
      setRevealedSessionKey(null);
      setShowKey(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadStatus();
  }, []);

  const validateAndSave = async () => {
    const previousStatus = status;
    const value = normalizeGeminiCredentialInput(inputValue);
    const formatError = validateApiKeyFormat(value);
    if (formatError) {
      setError(formatError);
      setMessage(null);
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      await setGeminiApiKey(value);
      setShowKey(false);
      setRevealedSessionKey(null);
      const wasConfigured = previousStatus.configured;
      if (wasConfigured) {
        setMessage("Gemini API key updated successfully.");
        onNotification?.({
          variant: "success",
          title: "API Key Updated Successfully",
          description:
            "Your Gemini API key has been revalidated and updated. All future AI requests will use the new credential.",
          autoDismissMs: 5000,
        });
      } else {
        setMessage("Gemini API key updated successfully.");
        onNotification?.({
          variant: "success",
          title: "AI Configuration Complete",
          description:
            "Your Gemini API key has been securely configured for this session.",
          autoDismissMs: 5000,
        });
      }
      await loadStatus();
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to validate Gemini API key.";
      setError(message);

      onNotification?.({
        variant: "error",
        title: previousStatus.configured
          ? "Unable to Update API Key"
          : "Unable to Configure API Key",
        description:
          "The provided Gemini credential could not be validated. Please verify your key and try again.",
      });

      if (previousStatus.configured) {
        if (!showKey && previousStatus.masked_key) {
          setInputValue(previousStatus.masked_key);
        }
        if (showKey && revealedSessionKey) {
          setInputValue(revealedSessionKey);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const removeKey = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      await deleteGeminiApiKey();
      setShowKey(false);
      setRevealedSessionKey(null);
      setInputValue("");
      setMessage("Gemini API key removed from this session.");
      onNotification?.({
        variant: "warning",
        title: "API Key Removed",
        description:
          "Your AI configuration has been removed. AI-powered features will be unavailable until a new key is configured.",
        autoDismissMs: 5000,
      });
      await loadStatus();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to remove Gemini API key.",
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleKeyVisibility = async () => {
    if (showKey) {
      setShowKey(false);
      if (status.configured && status.masked_key) {
        setInputValue(status.masked_key);
      }
      return;
    }

    if (status.configured && status.source === "session") {
      if (!revealedSessionKey) {
        setLoading(true);
        setError(null);
        try {
          const reveal = await getGeminiApiKeyForReveal();
          setRevealedSessionKey(reveal.api_key);
          setInputValue(reveal.api_key);
        } catch (error) {
          setError(
            error instanceof Error
              ? error.message
              : "Unable to reveal Gemini API key.",
          );
          setLoading(false);
          return;
        } finally {
          setLoading(false);
        }
      } else {
        setInputValue(revealedSessionKey);
      }
    }

    setShowKey(true);
  };

  if (hideWhenConfigured && status.configured) {
    return (
      <Card className="border-emerald-500/40 bg-emerald-500/10">
        <CardContent className="space-y-3 p-5">
          <div className="inline-flex items-center gap-2 text-emerald-200">
            <CheckCircle2 className="h-[var(--icon-md)] w-[var(--icon-md)]" />
            <p className="text-base font-semibold">AI Configuration Complete</p>
          </div>
          <p className="text-sm text-emerald-100/90">
            Your Gemini API key has been securely configured for this session.
          </p>
          <p className="text-sm text-emerald-100/90">
            WalletMind is now ready to use all AI-powered features.
          </p>
          <p className="text-sm text-emerald-100/90">
            You can update or remove your API key anytime from AI Settings.
          </p>
          <Button asChild variant="secondary" size="sm">
            <Link to="/app/settings?section=ai">Open AI Settings</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="inline-flex items-center gap-2 text-lg">
          <KeyRound className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--primary)]" />
          Configure Gemini API Key
        </CardTitle>
        <CardDescription>
          WalletMind uses your own Gemini API key. Your key is securely stored
          only for this session and removed when you log out.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
            <p className="text-xs text-[var(--text-muted)]">Status</p>
            <div className="mt-1">
              <StatusBadge
                label={status.configured ? "Configured" : "Not Configured"}
                tone={status.configured ? "healthy" : "warning"}
              />
            </div>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
            <p className="text-xs text-[var(--text-muted)]">Source</p>
            <p className="mt-1 text-sm font-medium capitalize">
              {status.source}
            </p>
          </div>
          {!compact ? (
            <>
              <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                <p className="text-xs text-[var(--text-muted)]">Model</p>
                <p className="mt-1 text-sm font-medium">{status.model}</p>
              </div>
              <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                <p className="text-xs text-[var(--text-muted)]">
                  Last validated
                </p>
                <p className="mt-1 text-sm font-medium">
                  {formatLastValidated(status.last_validated)}
                </p>
              </div>
            </>
          ) : null}
        </div>

        <div className="space-y-2">
          <label
            htmlFor="gemini-api-key"
            className="text-sm text-[var(--text-muted)]"
          >
            Gemini API Key (Google AI Studio)
          </label>
          <p className="text-xs text-[var(--text-muted)]">
            Use a Gemini credential starting with AIza or AQ.
          </p>
          <a
            href="https://aistudio.google.com/app/apikey"
            target="_blank"
            rel="noreferrer"
            className="inline-flex text-xs font-medium text-[var(--primary)] underline-offset-2 hover:underline"
          >
            Get API Key
          </a>
          <div className="flex gap-2">
            <Input
              id="gemini-api-key"
              ref={inputRef}
              type={showKey ? "text" : "password"}
              placeholder={
                status.configured
                  ? "••••••••••••••••••••••"
                  : "Paste your Gemini API key"
              }
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
            <Button
              type="button"
              variant="secondary"
              aria-label={showKey ? "Hide API key" : "Show API key"}
              onClick={() => void toggleKeyVisibility()}
              disabled={loading}
            >
              {showKey ? (
                <EyeOff className="h-[var(--icon-md)] w-[var(--icon-md)]" />
              ) : (
                <Eye className="h-[var(--icon-md)] w-[var(--icon-md)]" />
              )}
            </Button>
          </div>
        </div>

        {showInlineFeedback && error ? (
          <p className="text-sm text-rose-300">{error}</p>
        ) : null}
        {showInlineFeedback && message ? (
          <p className="text-sm text-emerald-200">{message}</p>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            onClick={() => void validateAndSave()}
            disabled={loading}
          >
            {status.configured ? "Update Key" : "Save"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setConfirmRemoveOpen(true)}
            disabled={loading || !status.configured}
          >
            Remove Key
          </Button>
        </div>
      </CardContent>
      <ConfirmationDialog
        open={confirmRemoveOpen}
        title="Remove API Key"
        description="Remove your configured Gemini API key?"
        cancelLabel="Cancel"
        confirmLabel="Confirm"
        variant="danger"
        onCancel={() => setConfirmRemoveOpen(false)}
        onConfirm={() => {
          setConfirmRemoveOpen(false);
          void removeKey();
        }}
        isConfirming={loading}
      />
    </Card>
  );
}
