import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import {
  REMEMBERED_PROFILES_STORAGE_KEY,
  USER_STORAGE_KEY,
} from "@/lib/auth/storage";
import { Sidebar } from "@/components/layout/sidebar";

describe("Sidebar", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders all expected navigation destinations", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "/app/home",
    );
    expect(screen.getByRole("link", { name: "Statements" })).toHaveAttribute(
      "href",
      "/app/statements",
    );
    expect(
      screen.getByRole("link", { name: "🤖 Agent Playground" }),
    ).toHaveAttribute("href", "/app/agent-playground");
    expect(screen.getByRole("link", { name: "Judge Hub" })).toHaveAttribute(
      "href",
      "/app/judge",
    );
    expect(screen.getByRole("link", { name: "AI Dashboard" })).toHaveAttribute(
      "href",
      "/app/dashboard",
    );
    expect(
      screen.getByRole("link", { name: "Spending Insights" }),
    ).toHaveAttribute("href", "/app/insights");
    expect(
      screen.getByRole("link", { name: "Budget Recommendations" }),
    ).toHaveAttribute("href", "/app/budget");
    expect(
      screen.getByRole("link", { name: "Financial Health" }),
    ).toHaveAttribute("href", "/app/health");
    expect(
      screen.getByRole("link", { name: "Monthly Report" }),
    ).toHaveAttribute("href", "/app/planner");
    expect(screen.getByRole("link", { name: "AI Assistant" })).toHaveAttribute(
      "href",
      "/app/assistant",
    );
    expect(screen.getByRole("link", { name: "Settings" })).toHaveAttribute(
      "href",
      "/app/settings",
    );
  });

  it("keeps Statements item active on nested upload route", () => {
    render(
      <MemoryRouter initialEntries={["/app/statements/upload"]}>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Statements" })).toHaveClass(
      "bg-[var(--primary-soft)]",
    );
  });

  it("logout clears only active user session", async () => {
    localStorage.setItem(
      USER_STORAGE_KEY,
      JSON.stringify({
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya",
        occupation: "Engineer",
        monthly_income: 120000,
        currency: "INR",
      }),
    );
    localStorage.setItem(
      REMEMBERED_PROFILES_STORAGE_KEY,
      JSON.stringify([
        {
          id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
          name: "Priya",
          occupation: "Engineer",
          monthly_income: 120000,
          currency: "INR",
        },
      ]),
    );
    localStorage.setItem("walletmind_ai_configured", "true");
    localStorage.setItem("walletmind_ai_source", "session");

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    await waitFor(() => {
      expect(localStorage.getItem(USER_STORAGE_KEY)).toBeNull();
      expect(localStorage.getItem("walletmind_ai_configured")).toBeNull();
      expect(localStorage.getItem("walletmind_ai_source")).toBeNull();
      expect(
        localStorage.getItem(REMEMBERED_PROFILES_STORAGE_KEY),
      ).not.toBeNull();
    });
  });
});
