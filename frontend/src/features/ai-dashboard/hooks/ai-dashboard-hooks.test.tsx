import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  useBudgetRecommendations,
  useHealthScore,
  useInsights,
  useMonthlyReport,
} from "@/features/ai-dashboard/hooks";
import * as dashboardApi from "@/features/ai-dashboard/services/ai-dashboard-api";

vi.mock("@/features/ai-dashboard/services/ai-dashboard-api", () => ({
  getBudgetRecommendations: vi.fn(),
  getHealthScore: vi.fn(),
  getInsights: vi.fn(),
  getMonthlyReport: vi.fn(),
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
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("AI dashboard hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads health score with React Query", async () => {
    vi.mocked(dashboardApi.getHealthScore).mockResolvedValue({
      overall_score: 70,
      grade: "B",
      components: {
        savings_rate: 70,
        income_stability: 70,
        spending_discipline: 70,
        recurring_obligations: 70,
        cash_flow: 70,
      },
      strengths: [],
      weaknesses: [],
      ai_explanation: "Good baseline.",
      recommendations: [],
    });

    const { result } = renderHook(() => useHealthScore("stmt-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(dashboardApi.getHealthScore).toHaveBeenCalledWith("stmt-1");
  });

  it("loads insights with React Query", async () => {
    vi.mocked(dashboardApi.getInsights).mockResolvedValue({
      statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
      deterministic_summary: {},
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
    });

    const { result } = renderHook(() => useInsights("stmt-2"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(dashboardApi.getInsights).toHaveBeenCalledWith("stmt-2");
  });

  it("loads budget recommendations with React Query", async () => {
    vi.mocked(dashboardApi.getBudgetRecommendations).mockResolvedValue({
      monthly_budget: {},
      overall_potential_savings: 250,
      priority_recommendations: [],
      ai_summary: "Summary",
      ai_recommendations: [],
    });

    const { result } = renderHook(() => useBudgetRecommendations("stmt-3"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(dashboardApi.getBudgetRecommendations).toHaveBeenCalledWith(
      "stmt-3",
    );
  });

  it("loads monthly report with React Query", async () => {
    vi.mocked(dashboardApi.getMonthlyReport).mockResolvedValue({
      executive_summary: "Report",
      financial_health: {},
      income_summary: {},
      expense_summary: {},
      cash_flow: {},
      spending_insights: {},
      budget_recommendations: {},
      health_score: {},
      strengths: [],
      risks: [],
      action_plan: [],
    });

    const { result } = renderHook(() => useMonthlyReport("stmt-4"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(dashboardApi.getMonthlyReport).toHaveBeenCalledWith("stmt-4");
  });
});
