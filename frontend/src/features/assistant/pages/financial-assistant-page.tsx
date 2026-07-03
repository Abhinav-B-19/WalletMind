import { useCallback, useEffect, useMemo, useState } from "react";
import { Eraser } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";
import {
  AssistantHero,
  ChatInput,
  ChatWindow,
  ConversationSidebar,
  SuggestedQuestionCard,
} from "@/features/assistant/components";
import { useAssistantChat } from "@/features/assistant/hooks/use-assistant-chat";
import type {
  AssistantChatResponse,
  ConversationMessage,
} from "@/features/assistant/types";
import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";
import { EmptyStateCard } from "@/features/ai-dashboard/components/empty-state-card";
import { ErrorCard } from "@/features/ai-dashboard/components/error-card";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import { useProcessedStatements } from "@/features/ai-dashboard/hooks";
import { isAIUnavailableError } from "@/features/ai-dashboard/services/ai-degradation";
import { getStoredUser } from "@/lib/auth/storage";

const SUGGESTED_QUESTIONS = [
  "How much did I spend on Swiggy?",
  "Where am I overspending?",
  "What subscriptions do I have?",
  "How much did I spend on fuel?",
  "Which category increased the most?",
  "Can I save more next month?",
];

const ASSISTANT_UNAVAILABLE_TITLE = "AI Assistant temporarily unavailable";
const ASSISTANT_UNAVAILABLE_DESCRIPTION =
  "AI responses are temporarily unavailable due to the current API usage limit or service availability. Core WalletMind features remain available. Please try again later.";

function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function nowLabel(): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function toMessage({
  role,
  text,
  response = null,
}: {
  role: "user" | "assistant";
  text: string;
  response?: AssistantChatResponse | null;
}): ConversationMessage {
  const id = `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  return {
    id,
    role,
    text,
    timestamp: nowLabel(),
    confidence: response?.confidence,
    sources: response?.sources,
  };
}

export function FinancialAssistantPage() {
  const user = getStoredUser();
  const [searchParams] = useSearchParams();
  const statementFromQuery = searchParams.get("statement_id");
  const [selectedStatementUuid, setSelectedStatementUuid] = useState<
    string | null
  >(statementFromQuery);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  const statementsQuery = useProcessedStatements(user?.id);
  const assistantChat = useAssistantChat();

  useEffect(() => {
    if (
      !selectedStatementUuid &&
      statementsQuery.data &&
      statementsQuery.data.length > 0
    ) {
      setSelectedStatementUuid(statementsQuery.data[0].statement_uuid);
    }
  }, [selectedStatementUuid, statementsQuery.data]);

  useEffect(() => {
    if (statementFromQuery) {
      setSelectedStatementUuid(statementFromQuery);
    }
  }, [statementFromQuery]);

  const aiUnavailable =
    assistantChat.isError && isAIUnavailableError(assistantChat.error);

  const selectedStatementLabel = useMemo(() => {
    if (!selectedStatementUuid || !statementsQuery.data) {
      return "Not selected";
    }

    const statement = statementsQuery.data.find(
      (item) => item.statement_uuid === selectedStatementUuid,
    );
    return statement?.original_filename ?? "Not selected";
  }, [selectedStatementUuid, statementsQuery.data]);

  const submitQuestion = useCallback(async () => {
    if (!selectedStatementUuid || !input.trim() || assistantChat.isPending) {
      return;
    }

    const question = input.trim();
    setInput("");

    setMessages((current) => [
      ...current,
      toMessage({ role: "user", text: question }),
    ]);

    try {
      const response = await assistantChat.mutateAsync({
        statement_id: selectedStatementUuid,
        question,
      });

      setMessages((current) => [
        ...current,
        toMessage({
          role: "assistant",
          text: response.answer,
          response,
        }),
      ]);
    } catch {
      // UI error state is handled by query state below.
    }
  }, [assistantChat, input, selectedStatementUuid]);

  const clearConversation = () => {
    setMessages([]);
    assistantChat.reset();
  };

  const askAgain = () => {
    const lastUser = [...messages]
      .reverse()
      .find((message) => message.role === "user");
    if (lastUser) {
      setInput(lastUser.text);
    }
  };

  const copyResponse = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard is best-effort.
    }
  };

  if (statementsQuery.isLoading) {
    return (
      <div className="space-y-6" aria-label="Assistant page loading">
        <PageTitle
          title="AI Financial Assistant"
          subtitle="Loading your assistant workspace."
        />
      </div>
    );
  }

  if (statementsQuery.isError) {
    return (
      <div className="space-y-6" aria-label="Assistant page error">
        <PageTitle
          title="AI Financial Assistant"
          subtitle="Production-grade conversational intelligence over your statement data."
        />
        <ErrorCard
          title="Unable to load processed statements"
          message={
            statementsQuery.error instanceof Error
              ? statementsQuery.error.message
              : "Please retry to continue."
          }
          onRetry={() => void statementsQuery.refetch()}
        />
      </div>
    );
  }

  if (!statementsQuery.data || statementsQuery.data.length === 0) {
    return (
      <div className="space-y-6" aria-label="Assistant page empty state">
        <PageTitle
          title="AI Financial Assistant"
          subtitle="Production-grade conversational intelligence over your statement data."
        />
        <EmptyStateCard
          title="No Processed Statement Found"
          description="Upload and process a statement to ask grounded assistant questions."
          ctaLabel="Upload Statement"
          ctaHref="/app/statements/upload"
          ariaLabel="No processed statements for assistant"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6" aria-label="Financial assistant page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageTitle
          title="AI Financial Assistant"
          subtitle="Production-grade conversational intelligence over your statement data."
        />
        <Button asChild variant="secondary">
          <Link to="/app/dashboard">Back to AI Dashboard</Link>
        </Button>
      </div>

      <AssistantHero
        status={assistantChat.isPending ? "Generating" : "Ready"}
        selectedStatementLabel={selectedStatementLabel}
      />

      <SectionCard
        title="Conversation Setup"
        description="Choose statement context and start from suggested prompts."
      >
        <div
          className="grid gap-4 lg:grid-cols-[1.2fr_1fr]"
          aria-label="Conversation setup grid"
        >
          <label className="space-y-2" htmlFor="assistant-statement-selector">
            <span className="text-sm text-[var(--text-muted)]">Statement</span>
            <select
              id="assistant-statement-selector"
              aria-label="Assistant statement selector"
              className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
              value={selectedStatementUuid ?? ""}
              onChange={(event) => setSelectedStatementUuid(event.target.value)}
            >
              {statementsQuery.data.map((statement) => (
                <option
                  key={statement.statement_uuid}
                  value={statement.statement_uuid}
                >
                  {statement.original_filename}
                </option>
              ))}
            </select>
          </label>

          <div className="space-y-2" aria-label="Suggested questions">
            <p className="text-sm text-[var(--text-muted)]">
              Suggested Questions
            </p>
            <div className="grid gap-2">
              {SUGGESTED_QUESTIONS.map((question) => (
                <SuggestedQuestionCard
                  key={question}
                  question={question}
                  onClick={setInput}
                />
              ))}
            </div>
          </div>
        </div>
      </SectionCard>

      {aiUnavailable ? (
        <AIUnavailableCard
          title={ASSISTANT_UNAVAILABLE_TITLE}
          description={ASSISTANT_UNAVAILABLE_DESCRIPTION}
          onRetry={() => assistantChat.reset()}
        />
      ) : null}

      {assistantChat.isError && !aiUnavailable ? (
        <ErrorCard
          title="Assistant request failed"
          message="Unable to generate a response right now. Please try again."
          onRetry={() => assistantChat.reset()}
        />
      ) : null}

      <section
        className="grid gap-4 xl:grid-cols-[2fr_1fr]"
        aria-label="Conversation layout grid"
      >
        <div className="space-y-4">
          <ChatWindow
            messages={messages}
            isGenerating={assistantChat.isPending}
            currencyFormatter={(value) =>
              formatCurrency(value, user?.currency ?? "USD")
            }
            onCopy={copyResponse}
            onAskAgain={askAgain}
          />

          <ChatInput
            value={input}
            disabled={assistantChat.isPending || !selectedStatementUuid}
            onChange={setInput}
            onSubmit={() => {
              void submitQuestion();
            }}
          />

          <div
            className="flex flex-wrap justify-end gap-2"
            aria-label="Conversation quick actions"
          >
            <Button
              type="button"
              variant="secondary"
              onClick={clearConversation}
            >
              <Eraser className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              Clear conversation
            </Button>
          </div>
        </div>

        <ConversationSidebar messageCount={messages.length} />
      </section>
    </div>
  );
}
