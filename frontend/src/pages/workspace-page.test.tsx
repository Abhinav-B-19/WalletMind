import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, beforeEach } from "vitest";

import { WorkspacePage } from "@/pages/workspace-page";

describe("WorkspacePage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders stored currency and primary goal", () => {
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya Sharma",
        occupation: "Engineer",
        monthly_income: 120000,
        currency: "INR",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );

    render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    expect(screen.getByText("INR")).toBeInTheDocument();
    expect(screen.getByText("Build Emergency Fund")).toBeInTheDocument();
  });
});
