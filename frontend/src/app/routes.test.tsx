import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { appRoutes } from "@/app/routes";

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
