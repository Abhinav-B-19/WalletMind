import { KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";

type ChatInputProps = {
  value: string;
  disabled: boolean;
  onChange: (next: string) => void;
  onSubmit: () => void;
};

export function ChatInput({
  value,
  disabled,
  onChange,
  onSubmit,
}: ChatInputProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter") {
      return;
    }

    if (event.shiftKey) {
      return;
    }

    event.preventDefault();
    onSubmit();
  };

  return (
    <div className="space-y-2" aria-label="Chat input section">
      <label
        htmlFor="assistant-input"
        className="text-sm text-[var(--text-muted)]"
      >
        Ask a financial question
      </label>
      <textarea
        id="assistant-input"
        aria-label="Assistant message input"
        className="min-h-24 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
        value={value}
        disabled={disabled}
        placeholder="Type your question..."
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-[var(--text-muted)]">
          Press Enter to send, Shift+Enter for newline.
        </p>
        <Button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
        >
          Send
        </Button>
      </div>
    </div>
  );
}
