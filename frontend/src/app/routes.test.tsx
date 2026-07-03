import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { appRoutes } from "@/app/routes";

vi.mock("@/features/ai-dashboard/hooks", () => ({
  useHealthScore: () => ({
    isLoading: true,
    isError: false,
    data: undefined,
    error: null,
    refetch: vi.fn(),
  }),
  useProcessedStatements: () => ({
    isLoading: false,
    isError: false,
    data: [
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        original_filename: "statement.csv",
      },
    ],
    error: null,
    refetch: vi.fn(),
  }),
  useInsights: () => ({
    isLoading: false,
    isError: false,
    dataUpdatedAt: 1762406400000,
    data: {
      statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
      deterministic_summary: {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        transaction_count: 1,
        credit_count: 0,
        debit_count: 1,
        cash_flow: {
          total_income: 0,
          total_expenses: 100,
          net_cash_flow: -100,
          savings_rate: 0,
        },
        category_breakdown: { Food: 100 },
        top_spending_categories: [{ category: "Food", amount: 100 }],
        top_merchants: [{ merchant: "Cafe", amount: 100 }],
        largest_expense: {
          date: "2026-07-01",
          amount: 100,
          category: "Food",
          merchant: "Cafe",
        },
        largest_income: null,
        monthly_averages: {
          income: 0,
          expenses: 100,
          net: -100,
        },
        monthly_trend: [
          { month: "2026-06", income: 0, expenses: 100, net: -100 },
        ],
        recurring_subscriptions: [],
      },
      insights: {
        summary: "Summary",
        strengths: [],
        concerns: [],
        recommendations: [],
      },
      model: "gemini",
      prompt_tokens: 1,
      completion_tokens: 1,
      total_tokens: 2,
      finish_reason: "stop",
    },
    error: null,
    refetch: vi.fn(),
  }),
  useBudgetRecommendations: () => ({
    isLoading: false,
    isError: false,
    dataUpdatedAt: 1762406400000,
    data: {
      monthly_budget: {
        Food: {
          historical: 120,
          recommended: 100,
          potential_saving: 20,
        },
      },
      overall_potential_savings: 20,
      priority_recommendations: [],
      ai_summary: "Summary",
      ai_recommendations: [],
    },
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("@/context/global-loader-context", () => ({
  useGlobalLoader: () => ({
    showLoader: () => undefined,
    hideLoader: () => undefined,
  }),
  GlobalLoaderProvider: ({ children }: { children: React.ReactNode }) =>
    children,
}));

describe("routing", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("upload page loads for authenticated users", async () => {
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "user-123",
        name: "Route Tester",
        occupation: "QA",
        monthly_income: 5000,
        currency: "USD",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );

    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/app/statements/upload"],
    });

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole("heading", {
        name: "Statement Upload Workspace",
      }),
    ).toBeInTheDocument();
  });

  it("library page loads for authenticated users", async () => {
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "user-123",
        name: "Route Tester",
        occupation: "QA",
        monthly_income: 5000,
        currency: "USD",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );

    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/app/statements"],
    });

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole("heading", { name: "Statement Library" }),
    ).toBeInTheDocument();
  });

  it("financial health page loads for authenticated users", async () => {
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "user-123",
        name: "Route Tester",
        occupation: "QA",
        monthly_income: 5000,
        currency: "USD",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );

    const router = createMemoryRouter(appRoutes, {
      initialEntries: [
        "/app/health?statement_id=8fe70b89-2325-42b6-82a6-16c6268d56eb",
      ],
    });

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole("heading", { name: "Financial Health" }),
    ).toBeInTheDocument();
  });

  it("insights page loads for authenticated users", async () => {
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "user-123",
        name: "Route Tester",
        occupation: "QA",
        monthly_income: 5000,
        currency: "USD",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );

    const router = createMemoryRouter(appRoutes, {
      initialEntries: [
        "/app/insights?statement_id=8fe70b89-2325-42b6-82a6-16c6268d56eb",
      ],
    });

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole("heading", { name: "Spending Insights" }),
    ).toBeInTheDocument();
  });

  it("budget page loads for authenticated users", async () => {
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "user-123",
        name: "Route Tester",
        occupation: "QA",
        monthly_income: 5000,
        currency: "USD",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );

    const router = createMemoryRouter(appRoutes, {
      initialEntries: [
        "/app/budget?statement_id=8fe70b89-2325-42b6-82a6-16c6268d56eb",
      ],
    });

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole("heading", {
        name: "Budget Recommendations",
        level: 2,
      }),
    ).toBeInTheDocument();
  });

  it("protected route redirects unauthenticated user", async () => {
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/app/statements"],
    });

    render(<RouterProvider router={router} />);

    expect(
      await screen.findByRole("heading", { name: "WalletMind" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Get Started" }),
    ).toBeInTheDocument();
  });
});
