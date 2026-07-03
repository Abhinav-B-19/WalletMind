import { Copy, RefreshCw, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SourceCard } from "@/features/assistant/components/source-card";
import type { ConversationMessage } from "@/features/assistant/types";

type ChatMessageProps = {
  message: ConversationMessage;
  currencyFormatter: (value: number) => string;
  onCopy: (text: string) => void;
  onAskAgain: () => void;
};

export function ChatMessage({
  message,
  currencyFormatter,
  onCopy,
  onAskAgain,
}: ChatMessageProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}
      aria-label={`${message.role} message`}
    >
      <Card
        className={`max-w-[90%] ${
          isAssistant
            ? "border-[var(--border)] bg-[var(--surface)]"
            : "border-[#4f8df7]/40 bg-[#4f8df7]/10"
        }`}
      >
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="inline-flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <UserRound className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              {isAssistant ? "Assistant" : "You"}
            </div>
            <p className="text-xs text-[var(--text-muted)]">
              {message.timestamp}
            </p>
          </div>

          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.text}
          </p>

          {isAssistant && message.sources && message.sources.length > 0 ? (
            <div className="space-y-2" aria-label="Referenced transactions">
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                Referenced transactions
              </p>
              <div className="grid gap-2 md:grid-cols-2">
                {message.sources.map((source) => (
                  <SourceCard
                    key={source.transaction_id}
                    merchant={source.merchant}
                    amount={currencyFormatter(source.amount)}
                    date={source.date}
                    confidenceLabel={`Confidence ${(message.confidence ?? 0).toFixed(2)}`}
                  />
                ))}
              </div>
            </div>
          ) : null}

          {isAssistant ? (
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => onCopy(message.text)}
              >
                <Copy className="mr-1 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                Copy response
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={onAskAgain}
              >
                <RefreshCw className="mr-1 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                Ask again
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
