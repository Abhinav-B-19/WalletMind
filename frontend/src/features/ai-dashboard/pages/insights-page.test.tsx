import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { InsightsPage } from "@/features/ai-dashboard/pages/insights-page";
import {
  useInsights,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";
import { ApiClientError } from "@/lib/api/client";

vi.mock("@/lib/auth/storage", () => ({
  getStoredUser: () => ({
    id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
    name: "Priya",
    currency: "USD",
  }),
}));

vi.mock("@/features/ai-dashboard/hooks", () => ({
  useInsights: vi.fn(),
  useProcessedStatements: vi.fn(),
}));

function createWrapper(initialPath = "/app/insights") {
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

describe("InsightsPage", () => {
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

    vi.mocked(useInsights).mockReturnValue({
      isLoading: false,
      isError: false,
      dataUpdatedAt: 1762406400000,
      data: {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        deterministic_summary: {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          transaction_count: 10,
          credit_count: 3,
          debit_count: 7,
          cash_flow: {
            total_income: 5000,
            total_expenses: 3200,
            net_cash_flow: 1800,
            savings_rate: 36,
          },
          category_breakdown: {
            Housing: 1200,
            Food: 900,
          },
          top_spending_categories: [
            { category: "Housing", amount: 1200 },
            { category: "Food", amount: 900 },
          ],
          top_merchants: [
            { merchant: "ACME Market", amount: 600 },
            { merchant: "Metro Rent", amount: 1200 },
          ],
          largest_expense: {
            date: "2026-07-01",
            amount: 1200,
            category: "Housing",
            merchant: "Metro Rent",
          },
          largest_income: {
            date: "2026-07-02",
            amount: 3000,
            category: null,
            merchant: "Payroll",
          },
          monthly_averages: {
            income: 5000,
            expenses: 3200,
            net: 1800,
          },
          monthly_trend: [
            {
              month: "2026-05",
              income: 5000,
              expenses: 3000,
              net: 2000,
            },
            {
              month: "2026-06",
              income: 4900,
              expenses: 3200,
              net: 1700,
            },
          ],
          recurring_subscriptions: [
            { merchant: "Music+", amount: 15 },
            { merchant: "Video+", amount: 20 },
          ],
        },
        insights: {
          summary: "Expenses are stable with room to optimize subscriptions.",
          strengths: ["Savings rate is healthy"],
          concerns: ["Food spending is increasing"],
          recommendations: [
            {
              title: "Reduce discretionary food spend",
              description: "Set a weekly dining cap.",
              priority: "high",
            },
          ],
        },
        model: "gemini-2.5-flash",
        prompt_tokens: 100,
        completion_tokens: 120,
        total_tokens: 220,
        finish_reason: "stop",
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);
  });

  it("renders insights dashboard sections and charts", () => {
    render(<InsightsPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Spending Insights")).toBeInTheDocument();
    expect(screen.getByText("AI Spending Insights")).toBeInTheDocument();
    expect(screen.getByText("Key Insights")).toBeInTheDocument();
    expect(screen.getByLabelText("Insight charts")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Category spending chart"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Monthly spending trend chart"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Insights timeline")).toBeInTheDocument();
    expect(screen.getByLabelText("Insight action cards")).toBeInTheDocument();
  });

  it("renders loading skeleton state", () => {
    vi.mocked(useInsights).mockReturnValue({
      isLoading: true,
      isError: false,
      data: undefined,
      dataUpdatedAt: 0,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);

    render(<InsightsPage />, { wrapper: createWrapper() });

    expect(
      screen.getByLabelText("Insights page loading state"),
    ).toBeInTheDocument();
  });

  it("renders non-AI error card for generic failures", () => {
    vi.mocked(useInsights).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      dataUpdatedAt: 0,
      error: new Error("Service unavailable"),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);

    render(<InsightsPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Insights unavailable")).toBeInTheDocument();
    expect(screen.getByText("Service unavailable")).toBeInTheDocument();
  });

  it("reuses AIUnavailableCard for AI-specific failures", () => {
    vi.mocked(useInsights).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      dataUpdatedAt: 0,
      error: new ApiClientError("Rate limited", { code: "AI_RATE_LIMIT" }),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);

    render(<InsightsPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("AI insights temporarily unavailable"),
    ).toBeInTheDocument();
  });
});
