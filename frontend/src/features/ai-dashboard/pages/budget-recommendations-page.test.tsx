import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BudgetRecommendationsPage } from "@/features/ai-dashboard/pages/budget-recommendations-page";
import {
  useBudgetRecommendations,
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
  useBudgetRecommendations: vi.fn(),
  useProcessedStatements: vi.fn(),
}));

function createWrapper(initialPath = "/app/budget") {
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

describe("BudgetRecommendationsPage", () => {
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

    vi.mocked(useBudgetRecommendations).mockReturnValue({
      isLoading: false,
      isError: false,
      dataUpdatedAt: 1762406400000,
      data: {
        monthly_budget: {
          Housing: {
            historical: 1500,
            recommended: 1200,
            potential_saving: 300,
          },
          Food: {
            historical: 850,
            recommended: 700,
            potential_saving: 150,
          },
          Transport: {
            historical: 300,
            recommended: 320,
            potential_saving: 0,
          },
        },
        overall_potential_savings: 450,
        priority_recommendations: [
          {
            title: "Reduce dining out",
            priority: "high",
            category: "Food",
            estimated_monthly_saving: 150,
          },
          {
            title: "Review rent options",
            priority: "medium",
            category: "Housing",
            estimated_monthly_saving: 300,
          },
        ],
        ai_summary: "You can reduce housing and food leakage.",
        ai_recommendations: [
          "Set strict dining budget limits.",
          "Negotiate rent during renewal.",
        ],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useBudgetRecommendations>);
  });

  it("renders hero, overview, table, and charts", () => {
    render(<BudgetRecommendationsPage />, { wrapper: createWrapper() });

    expect(
      screen.getByRole("heading", {
        name: "Budget Recommendations",
        level: 2,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Potential Monthly Savings")).toBeInTheDocument();
    expect(screen.getByLabelText("Budget overview cards")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Budget comparison table"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Budget charts")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Budget versus actual chart"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Potential savings waterfall chart"),
    ).toBeInTheDocument();
  });

  it("renders loading skeleton state", () => {
    vi.mocked(useBudgetRecommendations).mockReturnValue({
      isLoading: true,
      isError: false,
      data: undefined,
      dataUpdatedAt: 0,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useBudgetRecommendations>);

    render(<BudgetRecommendationsPage />, { wrapper: createWrapper() });

    expect(
      screen.getByLabelText("Budget page loading state"),
    ).toBeInTheDocument();
  });

  it("renders non-AI error state", () => {
    vi.mocked(useBudgetRecommendations).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      dataUpdatedAt: 0,
      error: new Error("Service unavailable"),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useBudgetRecommendations>);

    render(<BudgetRecommendationsPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("Budget recommendations unavailable"),
    ).toBeInTheDocument();
    expect(screen.getByText("Service unavailable")).toBeInTheDocument();
  });

  it("reuses AIUnavailableCard and keeps deterministic data visible", () => {
    vi.mocked(useBudgetRecommendations).mockReturnValue({
      isLoading: false,
      isError: true,
      dataUpdatedAt: 1762406400000,
      data: {
        monthly_budget: {
          Housing: {
            historical: 1500,
            recommended: 1200,
            potential_saving: 300,
          },
        },
        overall_potential_savings: 300,
        priority_recommendations: [],
        ai_summary: "fallback summary",
        ai_recommendations: [],
      },
      error: new ApiClientError("AI timeout", { code: "AI_TIMEOUT" }),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useBudgetRecommendations>);

    render(<BudgetRecommendationsPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("AI insights temporarily unavailable"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Budget comparison table"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("AI unavailable deterministic notice"),
    ).toBeInTheDocument();
  });

  it("uses responsive layout classes for dashboard sections", () => {
    const { container } = render(<BudgetRecommendationsPage />, {
      wrapper: createWrapper(),
    });

    const overviewGrid = screen.getByLabelText("Budget overview cards");
    expect(overviewGrid.className).toContain("sm:grid-cols-2");
    expect(overviewGrid.className).toContain("xl:grid-cols-4");

    const chartsGrid = screen.getByLabelText("Budget charts");
    expect(chartsGrid.className).toContain("xl:grid-cols-2");

    expect(container.querySelector("table")).toBeInTheDocument();
  });
});
