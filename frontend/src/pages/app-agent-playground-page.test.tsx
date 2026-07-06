import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AppAgentPlaygroundPage } from "@/pages/app-agent-playground-page";

const listStatementsMock = vi.fn();
const executeAgentsMock = vi.fn();
const listUsersMock = vi.fn();

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
  listUsers: (...args: unknown[]) => listUsersMock(...args),
}));

const DEMO_QUERY =
  "Analyze my finances and provide a complete financial health assessment with spending insights, personalized budget recommendations, a monthly financial report, and actionable advice to improve my financial future.";

function renderPlayground() {
  return render(
    <MemoryRouter initialEntries={["/app/agent-playground"]}>
      <Routes>
        <Route path="/app/agent-playground" element={<AppAgentPlaygroundPage />} />
        <Route
          path="/app/statements/upload"
          element={<h1>Statement Upload Workspace</h1>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

function successCoordinatorPayload() {
  return {
    success: true,
    message: "Coordinator execution completed successfully.",
    data: {
      overall_status: "COMPLETED",
      decision_record: {
        intent: "analyze_finances",
        capabilities: [
          "financial_health",
          "insights",
          "budget",
          "monthly_report",
          "chat",
        ],
        selected_agents: [
          "health_agent",
          "insights_agent",
          "budget_agent",
          "report_agent",
          "assistant_agent",
        ],
        reason: "Complex intent detected; selected multi-agent execution plan.",
        execution_mode: "multi",
        execution_timestamp: "2026-07-06T12:00:00Z",
      },
      execution_trace: [
        {
          agent_name: "health_agent",
          status: "COMPLETED",
          execution_order: 1,
          duration_ms: 120,
          started_at: "2026-07-06T12:00:00Z",
          ended_at: "2026-07-06T12:00:00Z",
        },
      ],
      individual_agent_results: [
        {
          status: "COMPLETED",
          agent_name: "health_agent",
          errors: [],
          result: {
            result: {
              data: {
                overall_score: 84,
                grade: "B+",
                ai_explanation: "Healthy profile with moderate risk.",
              },
            },
          },
        },
      ],
      metadata: {
        workflow_name: "walletmind_root_workflow",
        selected_agent_count: 5,
        successful_agent_count: 5,
        failed_agent_count: 0,
        runner_integrated: true,
        workflow: { strategy: "sequential" },
      },
    },
  };
}

function warningCoordinatorPayload() {
  return {
    success: true,
    message: "Coordinator execution completed with warnings.",
    data: {
      overall_status: "COMPLETED",
      decision_record: {
        intent: "analyze_finances",
        execution_mode: "multi",
        execution_timestamp: "2026-07-06T12:00:00Z",
      },
      execution_trace: [
        {
          agent_name: "health_agent",
          status: "COMPLETED",
          execution_order: 1,
          duration_ms: 120,
          started_at: "2026-07-06T12:00:00Z",
          ended_at: "2026-07-06T12:00:00Z",
        },
      ],
      individual_agent_results: [
        { agent_name: "health_agent", status: "COMPLETED", errors: [], result: {} },
        { agent_name: "insights_agent", status: "COMPLETED", errors: [], result: {} },
        { agent_name: "budget_agent", status: "COMPLETED", errors: [], result: {} },
        { agent_name: "report_agent", status: "COMPLETED", errors: [], result: {} },
        {
          agent_name: "assistant_agent",
          status: "FAILED",
          errors: ["Agent timeout"],
          result: {},
        },
      ],
      metadata: {
        workflow_name: "walletmind_root_workflow",
        selected_agent_count: 5,
        successful_agent_count: 4,
        failed_agent_count: 1,
        runner_integrated: true,
      },
    },
  };
}

const reducedMotionListeners = new Set<(event: MediaQueryListEvent) => void>();

function setupAnimationAndScrollMocks() {
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
    configurable: true,
    value: vi.fn(),
  });

  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    callback(0);
    return 1;
  });

  vi.stubGlobal("cancelAnimationFrame", vi.fn());

  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)" ? false : false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: (_eventName: string, listener: (event: MediaQueryListEvent) => void) => {
        reducedMotionListeners.add(listener);
      },
      removeEventListener: (_eventName: string, listener: (event: MediaQueryListEvent) => void) => {
        reducedMotionListeners.delete(listener);
      },
      dispatchEvent: vi.fn(),
    })),
  );
}

function getScrollIntoViewMock() {
  return HTMLElement.prototype.scrollIntoView as unknown as ReturnType<typeof vi.fn>;
}

function findAutoDismissTimer(
  timeoutSpy: { mock: { calls: Array<[TimerHandler, number?]> } },
): (() => void) | null {
  for (let index = timeoutSpy.mock.calls.length - 1; index >= 0; index -= 1) {
    const [callback, delay] = timeoutSpy.mock.calls[index];
    if (delay === 5000 && typeof callback === "function") {
      return callback as () => void;
    }
  }

  return null;
}

describe("AppAgentPlaygroundPage - Sprint 2.3.4", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    setupAnimationAndScrollMocks();

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

    listUsersMock.mockResolvedValue([]);
    listStatementsMock.mockResolvedValue([
      {
        statement_uuid: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        original_filename: "processing.csv",
        uploaded_at: "2026-07-01T00:00:00Z",
        status: "processing",
        analysis_status: "processing",
      },
      {
        statement_uuid: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        original_filename: "ready.csv",
        uploaded_at: "2026-07-02T00:00:00Z",
        status: "ready_for_analysis",
        analysis_status: "ready_for_analysis",
      },
      {
        statement_uuid: "cccccccc-cccc-cccc-cccc-cccccccccccc",
        original_filename: "completed.csv",
        uploaded_at: "2026-07-03T00:00:00Z",
        status: "completed",
        analysis_status: "completed",
      },
    ]);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("renders demo banner and supports dismiss", async () => {
    const user = userEvent.setup();
    renderPlayground();

    expect(await screen.findByText("Demo Mode")).toBeInTheDocument();
    expect(
      screen.getByText(/WalletMind is pre-configured to demonstrate complete multi-agent financial analysis/i),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Dismiss demo banner" }));
    expect(screen.queryByText("Demo Mode")).not.toBeInTheDocument();
  });

  it("prefills default query", async () => {
    renderPlayground();

    const queryInput = (await screen.findByRole("textbox", {
      name: "Natural language query",
    })) as HTMLTextAreaElement;

    expect(queryInput.value).toBe(DEMO_QUERY);
  });

  it("auto-selects first processed statement and defaults to multi-agent", async () => {
    renderPlayground();

    const statementSelect = (await screen.findByRole("combobox", {
      name: "Statement selector",
    })) as HTMLSelectElement;

    await waitFor(() => {
      expect(statementSelect.value).toBe("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    });

    expect(screen.getByRole("radio", { name: "Multi Agent" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Single Agent" })).not.toBeChecked();
  });

  it("enables execute immediately when defaults are valid", async () => {
    renderPlayground();

    const executeButton = await screen.findByRole("button", {
      name: "Execute Agents",
    });

    await waitFor(() => {
      expect(executeButton).toBeEnabled();
    });
  });

  it("shows empty-state and upload CTA when no processed statements exist", async () => {
    listStatementsMock.mockResolvedValue([
      {
        statement_uuid: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        original_filename: "processing.csv",
        uploaded_at: "2026-07-01T00:00:00Z",
        status: "processing",
        analysis_status: "processing",
      },
      {
        statement_uuid: "dddddddd-dddd-dddd-dddd-dddddddddddd",
        original_filename: "failed.csv",
        uploaded_at: "2026-07-02T00:00:00Z",
        status: "failed",
        analysis_status: "failed",
      },
    ]);

    renderPlayground();

    expect(
      await screen.findByText(/Upload and process a bank statement to use the Agent Playground/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No processed statements available./i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Upload and process a statement first, then return here./i),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Execute Agents" })).toBeDisabled();
  });

  it("navigates to upload page from empty-state CTA", async () => {
    const user = userEvent.setup();

    listStatementsMock.mockResolvedValue([
      {
        statement_uuid: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        original_filename: "processing.csv",
        uploaded_at: "2026-07-01T00:00:00Z",
        status: "processing",
        analysis_status: "processing",
      },
    ]);

    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Go to Statement Upload" }));
    expect(
      await screen.findByRole("heading", { name: "Statement Upload Workspace" }),
    ).toBeInTheDocument();
  });

  it("allows user to edit query freely", async () => {
    const user = userEvent.setup();
    renderPlayground();

    const queryInput = (await screen.findByRole("textbox", {
      name: "Natural language query",
    })) as HTMLTextAreaElement;

    await user.clear(queryInput);
    await user.type(queryInput, "Custom query for judging");

    expect(queryInput.value).toBe("Custom query for judging");
  });

  it("allows user to change statement", async () => {
    const user = userEvent.setup();
    renderPlayground();

    const statementSelect = (await screen.findByRole("combobox", {
      name: "Statement selector",
    })) as HTMLSelectElement;

    await waitFor(() => {
      expect(statementSelect.value).toBe("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    });

    await user.selectOptions(
      statementSelect,
      "cccccccc-cccc-cccc-cccc-cccccccccccc",
    );

    expect(statementSelect.value).toBe("cccccccc-cccc-cccc-cccc-cccccccccccc");
  });

  it("allows user to change execution mode", async () => {
    const user = userEvent.setup();
    renderPlayground();

    await user.click(screen.getByRole("radio", { name: "Single Agent" }));

    expect(screen.getByRole("radio", { name: "Single Agent" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Multi Agent" })).not.toBeChecked();
  });

  it("still supports user selection when no logged-in user exists", async () => {
    const user = userEvent.setup();
    localStorage.clear();

    listUsersMock.mockResolvedValue([
      {
        id: "u-1",
        name: "User One",
        occupation: "Engineer",
        monthly_income: 1000,
        currency: "USD",
      },
      {
        id: "u-2",
        name: "User Two",
        occupation: "Designer",
        monthly_income: 1500,
        currency: "USD",
      },
    ]);

    listStatementsMock.mockImplementation((userUuid: string) => {
      if (userUuid === "u-2") {
        return Promise.resolve([
          {
            statement_uuid: "22222222-2222-2222-2222-222222222222",
            original_filename: "u2-ready.csv",
            uploaded_at: "2026-07-05T00:00:00Z",
            status: "ready_for_analysis",
            analysis_status: "ready_for_analysis",
          },
        ]);
      }

      return Promise.resolve([
        {
          statement_uuid: "11111111-1111-1111-1111-111111111111",
          original_filename: "u1-ready.csv",
          uploaded_at: "2026-07-04T00:00:00Z",
          status: "ready_for_analysis",
          analysis_status: "ready_for_analysis",
        },
      ]);
    });

    renderPlayground();

    const userSelect = (await screen.findByRole("combobox", {
      name: "User selector",
    })) as HTMLSelectElement;

    await waitFor(() => {
      expect(userSelect.value).toBe("u-1");
    });

    await user.selectOptions(userSelect, "u-2");

    await waitFor(() => {
      const statementSelect = screen.getByRole("combobox", {
        name: "Statement selector",
      }) as HTMLSelectElement;
      expect(statementSelect.value).toBe("22222222-2222-2222-2222-222222222222");
    });
  });

  it("keeps execution/dashboard flow unchanged and technical details collapsible", async () => {
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    await waitFor(() => {
      expect(executeAgentsMock).toHaveBeenCalledWith({
        query: DEMO_QUERY,
        user_id: "11111111-1111-1111-1111-111111111111",
        session_id: "walletmind-session",
        user_uuid: "11111111-1111-1111-1111-111111111111",
        inputs: {
          statement_uuid: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
          execution_mode: "multi_agent",
        },
      });
    });

    expect(
      await screen.findByRole("heading", { name: "Coordinator Summary" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Execution Timeline" })).toBeInTheDocument();

    await user.click(screen.getByText("Show raw coordinator JSON"));
    expect(screen.getByText(/"overall_status": "COMPLETED"/i)).toBeInTheDocument();
  });

  it("auto-scrolls to results after successful execution", async () => {
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    await waitFor(() => {
      expect(getScrollIntoViewMock()).toHaveBeenCalled();
    });

    expect(await screen.findByRole("heading", { name: "Results" })).toBeInTheDocument();
  });

  it("renders success toast with status and agent counts", async () => {
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    expect(await screen.findByText("Analysis Complete")).toBeInTheDocument();
    expect(
      screen.getByText("WalletMind successfully executed the selected AI agents."),
    ).toBeInTheDocument();
    expect(screen.getByText(/Overall status:/i)).toBeInTheDocument();
    expect(screen.getByText(/Successful agents:/i)).toBeInTheDocument();
    expect(screen.getByText(/Failed agents:/i)).toBeInTheDocument();
  });

  it("renders warning toast for partial failures", async () => {
    executeAgentsMock.mockResolvedValue(warningCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    expect(await screen.findByText("Analysis Completed with Warnings")).toBeInTheDocument();
    expect(
      screen.getByText("4 of 5 agents completed successfully."),
    ).toBeInTheDocument();
  });

  it("scrolls to results when View Results button is clicked", async () => {
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    await waitFor(() => {
      expect(getScrollIntoViewMock()).toHaveBeenCalledTimes(1);
    });

    await user.click(await screen.findByRole("button", { name: "View Results" }));

    expect(getScrollIntoViewMock()).toHaveBeenCalledTimes(2);
    expect(screen.queryByTestId("execution-toast")).not.toBeInTheDocument();
  });

  it("applies temporary highlight class on results section", async () => {
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    const resultsSection = await screen.findByTestId("results-section");
    expect(resultsSection.className).toMatch(/results-highlight/);
  });

  it("does not auto-scroll on failed network requests", async () => {
    executeAgentsMock.mockRejectedValue(new Error("Network unavailable"));

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    expect(
      await screen.findByText("Unable to execute agents right now."),
    ).toBeInTheDocument();
    expect(getScrollIntoViewMock()).not.toHaveBeenCalled();
    expect(screen.queryByTestId("execution-toast")).not.toBeInTheDocument();
  });

  it("shows coordinating loading text until execution resolves", async () => {
    let resolveExecution: ((payload: ReturnType<typeof successCoordinatorPayload>) => void) | undefined;
    executeAgentsMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveExecution = resolve;
        }),
    );

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));

    expect(
      await screen.findByRole("button", { name: /WalletMind is coordinating AI agents/i }),
    ).toBeDisabled();
    expect(
      screen.getByText(/WalletMind is orchestrating agents and collecting results/i),
    ).toBeInTheDocument();

    if (resolveExecution) {
      resolveExecution(successCoordinatorPayload());
    }

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Execute Agents" })).toBeEnabled();
    });
  });

  it("auto-dismisses success toast after 5 seconds", async () => {
    const timeoutSpy = vi.spyOn(window, "setTimeout");
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));
    expect(await screen.findByText("Analysis Complete")).toBeInTheDocument();

    const dismissCallback = findAutoDismissTimer(timeoutSpy);
    expect(dismissCallback).not.toBeNull();

    if (dismissCallback) {
      act(() => {
        dismissCallback();
      });
    }

    await waitFor(() => {
      expect(screen.queryByTestId("execution-toast")).not.toBeInTheDocument();
    });
  });

  it("auto-dismisses warning toast after 5 seconds", async () => {
    const timeoutSpy = vi.spyOn(window, "setTimeout");
    executeAgentsMock.mockResolvedValue(warningCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));
    expect(await screen.findByText("Analysis Completed with Warnings")).toBeInTheDocument();

    const dismissCallback = findAutoDismissTimer(timeoutSpy);
    expect(dismissCallback).not.toBeNull();

    if (dismissCallback) {
      act(() => {
        dismissCallback();
      });
    }

    await waitFor(() => {
      expect(screen.queryByTestId("execution-toast")).not.toBeInTheDocument();
    });
  });

  it("keeps API error notification visible after 5 seconds until manually dismissed", async () => {
    const timeoutSpy = vi.spyOn(window, "setTimeout");
    executeAgentsMock.mockRejectedValue(new Error("Network unavailable"));

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));
    expect(await screen.findByText("Unable to execute agents right now.")).toBeInTheDocument();

    expect(findAutoDismissTimer(timeoutSpy)).toBeNull();
    expect(screen.getByText("Unable to execute agents right now.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Dismiss error notification" }));
    expect(screen.queryByText("Unable to execute agents right now.")).not.toBeInTheDocument();
  });

  it("cancels auto-dismiss timer when toast is manually dismissed", async () => {
    const timeoutSpy = vi.spyOn(window, "setTimeout");
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");
    executeAgentsMock.mockResolvedValue(successCoordinatorPayload());

    const user = userEvent.setup();
    renderPlayground();

    await user.click(await screen.findByRole("button", { name: "Execute Agents" }));
    expect(await screen.findByText("Analysis Complete")).toBeInTheDocument();

    const dismissCallback = findAutoDismissTimer(timeoutSpy);
    expect(dismissCallback).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "Dismiss execution notification" }));
    expect(screen.queryByTestId("execution-toast")).not.toBeInTheDocument();

    expect(clearTimeoutSpy).toHaveBeenCalled();

    if (dismissCallback) {
      act(() => {
        dismissCallback();
      });
    }

    expect(screen.queryByTestId("execution-toast")).not.toBeInTheDocument();
  });
});
