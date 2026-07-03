import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FinancialHealthPage } from "@/features/ai-dashboard/pages/financial-health-page";
import { useHealthScore } from "@/features/ai-dashboard/hooks";
import { ApiClientError } from "@/lib/api/client";

vi.mock("@/features/ai-dashboard/hooks", () => ({
  useHealthScore: vi.fn(),
}));

function createWrapper(initialPath = "/app/health?statement_id=statement-1") {
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

describe("FinancialHealthPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useHealthScore).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        overall_score: 82,
        grade: "B",
        components: {
          savings_rate: 80,
          income_stability: 76,
          spending_discipline: 71,
          recurring_obligations: 66,
          cash_flow: 84,
        },
        strengths: ["Stable positive cash flow"],
        weaknesses: ["Recurring obligations are elevated"],
        ai_explanation:
          "You are maintaining a strong baseline with room to improve recurring costs.",
        recommendations: [
          "Cut at least one low-value subscription this month.",
          "Increase savings automation by 5% of income.",
        ],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useHealthScore>);
  });

  it("renders complete financial health experience", () => {
    render(<FinancialHealthPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Financial Health")).toBeInTheDocument();
    expect(screen.getByText("Health Score Overview")).toBeInTheDocument();
    expect(screen.getByText("Component Breakdown")).toBeInTheDocument();
    expect(screen.getByText("Strengths")).toBeInTheDocument();
    expect(screen.getByText("Weaknesses")).toBeInTheDocument();
    expect(screen.getByText("Recommendations")).toBeInTheDocument();
    expect(screen.getByText("Health Legend")).toBeInTheDocument();
    expect(screen.getByText("Grade B")).toBeInTheDocument();
  });

  it("shows loading skeleton state", () => {
    vi.mocked(useHealthScore).mockReturnValue({
      isLoading: true,
      isError: false,
      data: undefined,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useHealthScore>);

    render(<FinancialHealthPage />, { wrapper: createWrapper() });

    expect(
      screen.getByLabelText("Financial health page loading"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Loading financial health hero"),
    ).toBeInTheDocument();
  });

  it("shows friendly retry on error", () => {
    vi.mocked(useHealthScore).mockReturnValue({
      isLoading: false,
      isError: true,
      data: undefined,
      error: new Error("Service unavailable"),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useHealthScore>);

    render(<FinancialHealthPage />, { wrapper: createWrapper() });

    expect(
      screen.getByText("Unable to load financial health"),
    ).toBeInTheDocument();
    expect(screen.getByText("Service unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("shows AI unavailable card while preserving deterministic health data", () => {
    vi.mocked(useHealthScore).mockReturnValue({
      isLoading: false,
      isError: true,
      data: {
        overall_score: 82,
        grade: "B",
        components: {
          savings_rate: 80,
          income_stability: 76,
          spending_discipline: 71,
          recurring_obligations: 66,
          cash_flow: 84,
        },
        strengths: ["Stable positive cash flow"],
        weaknesses: ["Recurring obligations are elevated"],
        ai_explanation: "AI text",
        recommendations: ["AI recommendation"],
      },
      error: new ApiClientError("AI response invalid", {
        code: "AI_RESPONSE_INVALID",
      }),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useHealthScore>);

    render(<FinancialHealthPage />, { wrapper: createWrapper() });

    expect(screen.getByText("Grade B")).toBeInTheDocument();
    expect(screen.getByText("Component Breakdown")).toBeInTheDocument();
    expect(
      screen.getAllByText("AI insights temporarily unavailable").length,
    ).toBeGreaterThan(0);
  });

  it("renders empty state when statement id is missing", () => {
    render(<FinancialHealthPage />, { wrapper: createWrapper("/app/health") });

    expect(screen.getByText("No Statement Selected")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open AI Dashboard" }),
    ).toBeInTheDocument();
  });

  it("renders responsive metric grid and progress values", () => {
    render(<FinancialHealthPage />, { wrapper: createWrapper() });

    const grid = screen.getByLabelText("Health component grid");
    expect(grid.className).toContain("md:grid-cols-2");
    expect(grid.className).toContain("xl:grid-cols-3");

    const savingsProgress = screen.getByRole("progressbar", {
      name: "Savings Rate progress",
    });
    expect(savingsProgress).toHaveAttribute("aria-valuenow", "80");
  });
});
