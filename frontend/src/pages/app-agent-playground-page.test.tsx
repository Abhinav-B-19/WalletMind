import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppAgentPlaygroundPage } from "@/pages/app-agent-playground-page";

const listStatementsMock = vi.fn();
const executeAgentsMock = vi.fn();

vi.mock("@/lib/api/statements", () => ({
  listStatements: (...args: unknown[]) => listStatementsMock(...args),
}));

vi.mock("@/lib/api/agents", () => ({
  executeAgents: (...args: unknown[]) => executeAgentsMock(...args),
  executionModeSchema: {
    enum: {
      single: "single",
      multi: "multi",
    },
  },
}));

vi.mock("@/lib/api/users", () => ({
  listUsers: vi.fn(),
}));

describe("AppAgentPlaygroundPage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();

    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "11111111-1111-1111-1111-111111111111",
        name: "Demo User",
        occupation: "Analyst",
        monthly_income: 9000,
        currency: "USD",
        primary_financial_goal: "Improve savings",
      }),
    );

    listStatementsMock.mockResolvedValue([
      {
        statement_uuid: "22222222-2222-2222-2222-222222222222",
        original_filename: "statement.csv",
        uploaded_at: "2026-07-01T00:00:00Z",
        analysis_status: "ready_for_analysis",
      },
    ]);
  });

  it("submits execute request and renders raw response", async () => {
    executeAgentsMock.mockResolvedValue({
      success: true,
      message: "Coordinator execution completed successfully.",
      data: {
        summary: "Execution complete",
      },
    });

    const user = userEvent.setup();
    render(<AppAgentPlaygroundPage />);

    const queryInput = await screen.findByRole("textbox", {
      name: "Natural language query",
    });

    await user.type(queryInput, "Analyze my finances");
    await user.click(screen.getByRole("button", { name: "Execute Agents" }));

    await waitFor(() => {
      expect(executeAgentsMock).toHaveBeenCalledWith({
        query: "Analyze my finances",
        user_id: "11111111-1111-1111-1111-111111111111",
        session_id: "walletmind-session",
        user_uuid: "11111111-1111-1111-1111-111111111111",
        inputs: {
          statement_uuid: "22222222-2222-2222-2222-222222222222",
          execution_mode: "single_agent",
        },
      });
    });

    expect(
      await screen.findByRole("heading", { name: "Raw Coordinator Response" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Execution complete/i)).toBeInTheDocument();
  });
});
