import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FinancialAssistantPage } from "@/features/assistant/pages/financial-assistant-page";
import { useAssistantChat } from "@/features/assistant/hooks/use-assistant-chat";
import { useProcessedStatements } from "@/features/ai-dashboard/hooks";
import { ApiClientError } from "@/lib/api/client";

vi.mock("@/lib/auth/storage", () => ({
  getStoredUser: () => ({
    id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
    name: "Priya",
    currency: "USD",
  }),
}));

vi.mock("@/features/assistant/hooks/use-assistant-chat", () => ({
  useAssistantChat: vi.fn(),
}));

vi.mock("@/features/ai-dashboard/hooks", () => ({
  useProcessedStatements: vi.fn(),
}));

function createWrapper(initialPath = "/app/chat") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("FinancialAssistantPage", () => {
  const mutateAsync = vi.fn();
  const reset = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useProcessedStatements).mockReturnValue({
      isLoading: false,
      isError: false,
      data: [
        {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          stored_file_path: "/tmp/stored.csv",
          original_filename: "statement.csv",
          stored_filename: "stored.csv",
          file_size: 100,
          file_type: "csv",
          parser_type: "csv",
          bank_name: null,
          classification_confidence: 0.9,
          classification_method: "header-keyword",
          classified_at: "2026-07-03T09:00:01.000Z",
          parsed_transaction_count: 5,
          failed_transaction_count: 0,
          parsed_at: "2026-07-03T09:00:02.000Z",
          analysis_status: "ready_for_analysis",
          status: "ready_for_analysis",
          uploaded_at: "2026-07-03T09:00:00.000Z",
        },
      ],
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProcessedStatements>);

    mutateAsync.mockResolvedValue({
      answer: "You spent $320 on fuel this month.",
      confidence: 0.86,
      sources: [
        {
          transaction_id: "tx-1",
          merchant: "Fuel Station",
          amount: 320,
          date: "2026-07-01",
        },
      ],
    });

    vi.mocked(useAssistantChat).mockReturnValue({
      mutateAsync,
      isPending: false,
      isError: false,
      error: null,
      reset,
    } as unknown as ReturnType<typeof useAssistantChat>);
  });

  it("renders chat layout, suggested questions, and conversation sidebar", () => {
    render(<FinancialAssistantPage />, { wrapper: createWrapper() });

    expect(
      screen.getByRole("heading", { name: "AI Financial Assistant", level: 2 }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Suggested questions")).toBeInTheDocument();
    expect(screen.getByLabelText("Chat window")).toBeInTheDocument();
    expect(screen.getByText("Conversation Sidebar")).toBeInTheDocument();
  });

  it("suggested question populates input and sends chat message", async () => {
    render(<FinancialAssistantPage />, { wrapper: createWrapper() });

    fireEvent.click(
      screen.getByRole("button", { name: "How much did I spend on fuel?" }),
    );

    const input = screen.getByLabelText("Assistant message input");
    expect(input).toHaveValue("How much did I spend on fuel?");

    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1));

    expect(
      screen.getByText("You spent $320 on fuel this month."),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Referenced transactions"),
    ).toBeInTheDocument();
    expect(screen.getByText("Fuel Station")).toBeInTheDocument();
    expect(screen.getByText("Amount: $320")).toBeInTheDocument();
  });

  it("shows typing indicator while response is generating", () => {
    vi.mocked(useAssistantChat).mockReturnValue({
      mutateAsync,
      isPending: true,
      isError: false,
      error: null,
      reset,
    } as unknown as ReturnType<typeof useAssistantChat>);

    render(<FinancialAssistantPage />, { wrapper: createWrapper() });

    expect(
      screen.getByLabelText("Assistant typing indicator"),
    ).toBeInTheDocument();
  });

  it("shows assistant-specific AI unavailable card for AI failure codes", () => {
    vi.mocked(useAssistantChat).mockReturnValue({
      mutateAsync,
      isPending: false,
      isError: true,
      error: new ApiClientError("timeout", { code: "AI_TIMEOUT" }),
      reset,
    } as unknown as ReturnType<typeof useAssistantChat>);

    render(<FinancialAssistantPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("AI Assistant temporarily unavailable"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /AI responses are temporarily unavailable due to the current API usage limit or service availability/,
      ),
    ).toBeInTheDocument();
  });

  it("uses responsive layout classes for conversation section", () => {
    render(<FinancialAssistantPage />, { wrapper: createWrapper() });

    const setupGrid = screen.getByLabelText("Conversation setup grid");
    expect(setupGrid.className).toContain("grid");
    expect(setupGrid.className).toContain("lg:grid-cols");

    const conversationGrid = screen.getByLabelText("Conversation layout grid");
    expect(conversationGrid.className).toContain("grid");
    expect(conversationGrid.className).toContain("xl:grid-cols");

    const quickActions = screen.getByLabelText("Conversation quick actions");
    expect(quickActions.className).toContain("flex");
  });
});
