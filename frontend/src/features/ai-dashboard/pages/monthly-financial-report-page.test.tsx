import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MonthlyFinancialReportPage } from "@/features/ai-dashboard/pages/monthly-financial-report-page";
import {
  useBudgetRecommendations,
  useHealthScore,
  useInsights,
  useMonthlyReport,
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
  useProcessedStatements: vi.fn(),
  useMonthlyReport: vi.fn(),
  useHealthScore: vi.fn(),
  useInsights: vi.fn(),
  useBudgetRecommendations: vi.fn(),
}));

function createWrapper(initialPath = "/app/planner") {
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

describe("MonthlyFinancialReportPage", () => {
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

    vi.mocked(useMonthlyReport).mockReturnValue({
      isLoading: false,
      isError: false,
      dataUpdatedAt: 1762406400000,
      data: {
        executive_summary:
          "This month demonstrated stable income and controlled discretionary spending.",
        financial_health: {
          recommendations: ["Increase recurring savings transfers."],
        },
        income_summary: {
          total_income: 12000,
          average_monthly_income: 12000,
          largest_income_source: "Primary Salary",
          largest_income_sources: [{ source: "Primary Salary", amount: 12000 }],
        },
        expense_summary: {
          total_expenses: 6400,
          largest_expense_merchant: "Rent Corp",
          largest_expense: 2500,
          credit_count: 5,
          debit_count: 33,
        },
        cash_flow: {
          net_cash_flow: 5600,
          savings_rate: 46.6,
          monthly_trend: [
            { month: "2026-05", income: 12000, expenses: 6100, net: 5900 },
            { month: "2026-06", income: 12000, expenses: 6400, net: 5600 },
          ],
        },
        spending_insights: {
          recurring_payments: 2,
        },
        budget_recommendations: {},
        health_score: {
          overall_score: 82,
          grade: "A-",
          components: {
            savings_rate: 85,
            income_stability: 90,
            spending_discipline: 78,
            recurring_obligations: 72,
            cash_flow: 84,
          },
        },
        strengths: ["Strong net cash flow", "High income stability"],
        risks: ["Rising discretionary spend in dining"],
        action_plan: [
          "Set dining cap",
          "Review subscriptions",
          "Auto-invest surplus",
        ],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useMonthlyReport>);

    vi.mocked(useHealthScore).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        overall_score: 82,
        grade: "A-",
        components: {
          savings_rate: 85,
          income_stability: 90,
          spending_discipline: 78,
          recurring_obligations: 72,
          cash_flow: 84,
        },
        strengths: ["Strong net cash flow", "High income stability"],
        weaknesses: ["Discretionary dining has risen"],
        ai_explanation:
          "Healthy fundamentals with room to optimize recurring expenses.",
        recommendations: [
          "Increase monthly automatic savings transfer.",
          "Trim discretionary dining budget.",
          "Review recurring commitments quarterly.",
        ],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useHealthScore>);

    vi.mocked(useInsights).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        deterministic_summary: {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          transaction_count: 10,
          credit_count: 2,
          debit_count: 8,
          cash_flow: {
            total_income: 12000,
            total_expenses: 6400,
            net_cash_flow: 5600,
            savings_rate: 46.6,
          },
          category_breakdown: {
            Rent: 2500,
            Food: 900,
            Fuel: 600,
          },
          top_spending_categories: [
            { category: "Rent", amount: 2500 },
            { category: "Food", amount: 900 },
          ],
          top_merchants: [
            { merchant: "Rent Corp", amount: 2500 },
            { merchant: "Swiggy", amount: 600 },
          ],
          largest_expense: {
            date: "2026-06-01",
            amount: 2500,
            category: "Rent",
            merchant: "Rent Corp",
          },
          largest_income: {
            date: "2026-06-05",
            amount: 12000,
            category: "Salary",
            merchant: "Employer",
          },
          monthly_averages: {
            income: 12000,
            expenses: 6400,
            net: 5600,
          },
          monthly_trend: [
            { month: "2026-05", income: 12000, expenses: 6100, net: 5900 },
            { month: "2026-06", income: 12000, expenses: 6400, net: 5600 },
          ],
          recurring_subscriptions: [{ merchant: "Netflix", amount: 15 }],
        },
        insights: {
          summary:
            "Spending remains controlled with concentration in essential categories.",
          strengths: [],
          concerns: [],
          recommendations: [],
        },
        model: "gemini",
        prompt_tokens: 100,
        completion_tokens: 120,
        total_tokens: 220,
        finish_reason: "stop",
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);

    vi.mocked(useBudgetRecommendations).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        monthly_budget: {
          Food: {
            historical: 900,
            recommended: 760,
            potential_saving: 140,
          },
          Fuel: {
            historical: 600,
            recommended: 520,
            potential_saving: 80,
          },
        },
        overall_potential_savings: 220,
        priority_recommendations: [
          {
            title: "Reduce dining spend",
            priority: "high",
            category: "Food",
            estimated_monthly_saving: 140,
          },
        ],
        ai_summary: "Focus on variable expenses.",
        ai_recommendations: ["Review weekly discretionary spending."],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useBudgetRecommendations>);
  });

  it("renders flagship report sections and reused chart components", () => {
    render(<MonthlyFinancialReportPage />, { wrapper: createWrapper() });

    expect(
      screen.getByRole("heading", {
        name: "Monthly Financial Report",
        level: 2,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Report Cover")).toBeInTheDocument();
    expect(screen.getByText("Financial Health")).toBeInTheDocument();
    expect(screen.getByText("Income Overview")).toBeInTheDocument();
    expect(screen.getByText("Expense Overview")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Cash Flow", level: 3 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Budget Recommendations")).toBeInTheDocument();
    expect(screen.getByText("Spending Insights")).toBeInTheDocument();
    expect(screen.getByText("Financial Risks")).toBeInTheDocument();
    expect(screen.getByText("Action Plan")).toBeInTheDocument();

    expect(
      screen.getAllByText("Category & Payment Mix").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Cash Flow Trends").length).toBeGreaterThan(0);
    expect(screen.getByText("Budget vs Actual")).toBeInTheDocument();
  });

  it("shows loading state while statements are loading", () => {
    vi.mocked(useProcessedStatements).mockReturnValue({
      isLoading: true,
      isError: false,
      data: undefined,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProcessedStatements>);

    render(<MonthlyFinancialReportPage />, { wrapper: createWrapper() });

    expect(
      screen.getByLabelText("Monthly report page loading"),
    ).toBeInTheDocument();
  });

  it("shows error state when monthly report fails", () => {
    vi.mocked(useMonthlyReport).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      error: new Error("backend exploded"),
      dataUpdatedAt: 0,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useMonthlyReport>);

    render(<MonthlyFinancialReportPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Monthly report unavailable")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Report generation is temporarily unavailable. Please retry in a moment.",
      ),
    ).toBeInTheDocument();
  });

  it("shows AI unavailable fallback while deterministic sections remain", () => {
    vi.mocked(useInsights).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      error: new ApiClientError("timeout", { code: "AI_TIMEOUT" }),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useInsights>);

    render(<MonthlyFinancialReportPage />, { wrapper: createWrapper() });

    expect(
      screen.getAllByLabelText("AI unavailable card").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByLabelText("Deterministic fallback notice"),
    ).toBeInTheDocument();
  });

  it("includes responsive and print-ready layout classes", () => {
    render(<MonthlyFinancialReportPage />, { wrapper: createWrapper() });

    const coverLayout = screen.getByLabelText("Report cover layout");
    expect(coverLayout.className).toContain("grid");
    expect(coverLayout.className).toContain("xl:grid-cols");

    const root = screen.getByTestId("monthly-report-root");
    expect(root.className).toContain("print:space-y-4");
  });
});
