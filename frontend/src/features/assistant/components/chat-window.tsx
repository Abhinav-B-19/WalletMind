import { useEffect, useRef } from "react";

import { ChatMessage } from "@/features/assistant/components/chat-message";
import { TypingIndicator } from "@/features/assistant/components/typing-indicator";
import type { ConversationMessage } from "@/features/assistant/types";

type ChatWindowProps = {
  messages: ConversationMessage[];
  isGenerating: boolean;
  currencyFormatter: (value: number) => string;
  onCopy: (text: string) => void;
  onAskAgain: () => void;
};

export function ChatWindow({
  messages,
  isGenerating,
  currencyFormatter,
  onCopy,
  onAskAgain,
}: ChatWindowProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (typeof endRef.current?.scrollIntoView === "function") {
      endRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, isGenerating]);

  return (
    <div
      className="h-[32rem] overflow-y-auto rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-soft)] p-4"
      aria-label="Chat window"
    >
      <div className="space-y-3">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            currencyFormatter={currencyFormatter}
            onCopy={onCopy}
            onAskAgain={onAskAgain}
          />
        ))}

        {isGenerating ? <TypingIndicator /> : null}
      </div>
      <div ref={endRef} />
    </div>
  );
}
