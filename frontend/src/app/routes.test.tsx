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
