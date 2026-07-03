import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AIDashboardPage } from "@/features/ai-dashboard/pages/ai-dashboard-page";
import {
  useAIHealth,
  useBudgetRecommendations,
  useHealthScore,
  useInsights,
  useMonthlyReport,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";

vi.mock("@/lib/auth/storage", () => ({
  getStoredUser: () => ({
    id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
    name: "Priya",
    currency: "USD",
  }),
}));

vi.mock("@/features/ai-dashboard/hooks", () => ({
  useAIHealth: vi.fn(),
  useBudgetRecommendations: vi.fn(),
  useHealthScore: vi.fn(),
  useInsights: vi.fn(),
  useMonthlyReport: vi.fn(),
  useProcessedStatements: vi.fn(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("AIDashboardPage", () => {
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

    vi.mocked(useAIHealth).mockReturnValue({
      data: {
        configured: true,
        model: "gemini-2.5-flash",
        status: "healthy",
      },
    } as ReturnType<typeof useAIHealth>);

    vi.mocked(useHealthScore).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        overall_score: 78,
        grade: "B",
        components: {
          savings_rate: 80,
          income_stability: 74,
          spending_discipline: 70,
          recurring_obligations: 76,
          cash_flow: 80,
        },
        strengths: ["Strong savings trend"],
        weaknesses: ["Dining out is elevated"],
        ai_explanation:
          "Your spending trajectory is improving month over month.",
        recommendations: ["Cap dining budget at 15%"],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useHealthScore>);

    vi.mocked(useInsights).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        deterministic_summary: {},
        insights: {
          summary: "Spending is stable with room to optimize subscriptions.",
          strengths: [],
          concerns: [],
          recommendations: [
            {
              title: "Trim subscriptions",
              description: "Remove one underused subscription.",
              priority: "high",
            },
          ],
        },
        model: "gemini-2.5-flash",
        prompt_tokens: 1,
        completion_tokens: 1,
        total_tokens: 2,
        finish_reason: "stop",
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);

    vi.mocked(useBudgetRecommendations).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        monthly_budget: {},
        overall_potential_savings: 1200,
        priority_recommendations: [
          {
            title: "Reduce Food & Dining spending by 300 per month",
            category: "Food & Dining",
            priority: "high",
            estimated_monthly_saving: 300,
          },
        ],
        ai_summary: "Focus food and ride-sharing categories first.",
        ai_recommendations: [
          "Reduce subscriptions",
          "Meal prep",
          "Review rides",
        ],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useBudgetRecommendations>);

    vi.mocked(useMonthlyReport).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        executive_summary: "Net cash flow remains positive with stable income.",
        financial_health: {},
        income_summary: { total_income: 5000 },
        expense_summary: { total_expenses: 3200 },
        cash_flow: { net_cash_flow: 1800 },
        spending_insights: {},
        budget_recommendations: {},
        health_score: { grade: "B" },
        strengths: ["Consistent salary"],
        risks: ["Rising discretionary spend"],
        action_plan: ["Cap dining", "Review subscriptions"],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useMonthlyReport>);
  });

  it("renders dashboard sections and cards", async () => {
    render(<AIDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText("AI Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Financial Health Snapshot")).toBeInTheDocument();
    expect(screen.getByLabelText("Quick metrics")).toBeInTheDocument();
    expect(screen.getByText("AI Insights Preview")).toBeInTheDocument();
    expect(
      screen.getByText("Budget Recommendation Preview"),
    ).toBeInTheDocument();
    expect(screen.getByText("Financial Assistant")).toBeInTheDocument();
    expect(screen.getByText("Monthly Report Preview")).toBeInTheDocument();
  });

  it("shows loading state when statements are loading", () => {
    vi.mocked(useProcessedStatements).mockReturnValue({
      isLoading: true,
      isError: false,
      data: undefined,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProcessedStatements>);

    render(<AIDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByLabelText("AI dashboard loading")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Loading dashboard statements"),
    ).toBeInTheDocument();
  });

  it("shows error state when processed statements fail", () => {
    vi.mocked(useProcessedStatements).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      error: new Error("Boom"),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProcessedStatements>);

    render(<AIDashboardPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("Unable to load processed statements"),
    ).toBeInTheDocument();
    expect(screen.getByText("Boom")).toBeInTheDocument();
  });

  it("shows empty state when no processed statements are available", () => {
    vi.mocked(useProcessedStatements).mockReturnValue({
      isLoading: false,
      isError: false,
      data: [],
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProcessedStatements>);

    render(<AIDashboardPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("No Processed Statement Found"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Upload Statement" }),
    ).toBeInTheDocument();
  });
});
