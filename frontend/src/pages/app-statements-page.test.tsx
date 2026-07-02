import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { AppStatementsPage } from "@/pages/app-statements-page";
import * as statementsApi from "@/lib/api/statements";

vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );

  return {
    ...actual,
    Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
      <a href={to}>{children}</a>
    ),
    useLocation: () => ({ state: null }),
  };
});

vi.mock("@/context/global-loader-context", () => ({
  useGlobalLoader: () => ({
    showLoader: () => undefined,
    hideLoader: () => undefined,
  }),
}));

function makeStatement(
  statement_uuid: string,
  original_filename: string,
  uploaded_at: string,
  file_size = 77,
) {
  return {
    statement_uuid,
    stored_file_path: `/tmp/${statement_uuid}.csv`,
    original_filename,
    stored_filename: `${statement_uuid}.csv`,
    file_size,
    file_type: "csv",
    parser_type: "csv",
    bank_name: "Demo Bank",
    classification_confidence: 0.88,
    classification_method: "header-keyword",
    classified_at: "2026-07-03T09:00:01.000Z",
    analysis_status: "ready_for_parsing" as const,
    status: "ready_for_parsing" as const,
    uploaded_at,
  };
}

describe("AppStatementsPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem(
      "walletmind_user",
      JSON.stringify({
        id: "user-123",
        name: "Test User",
        occupation: "QA",
        monthly_income: 5000,
        currency: "USD",
        primary_financial_goal: "Build Emergency Fund",
      }),
    );
  });

  it("renders statements from API", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
      makeStatement("2", "beta.csv", "2026-07-02T10:00:00.000Z"),
    ]);

    render(<AppStatementsPage />);

    expect(await screen.findAllByText("alpha.csv")).toHaveLength(2);
    expect(screen.getAllByText("beta.csv")).toHaveLength(2);
  });

  it("filters statements by instant search", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "salary.csv", "2026-07-03T10:00:00.000Z"),
      makeStatement("2", "groceries.csv", "2026-07-02T10:00:00.000Z"),
    ]);

    render(<AppStatementsPage />);

    await screen.findAllByText("salary.csv");

    fireEvent.change(screen.getByLabelText("Search statements"), {
      target: { value: "groc" },
    });

    expect(screen.queryAllByText("salary.csv")).toHaveLength(0);
    expect(screen.getAllByText("groceries.csv")).toHaveLength(2);
  });

  it("sorts by filename", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "zeta.csv", "2026-07-03T10:00:00.000Z"),
      makeStatement("2", "alpha.csv", "2026-07-02T10:00:00.000Z"),
    ]);

    render(<AppStatementsPage />);

    await screen.findAllByText("zeta.csv");

    fireEvent.change(screen.getByLabelText("Sort statements"), {
      target: { value: "filename" },
    });

    const filenameCells = screen
      .getAllByTitle(/\.csv$/)
      .map((el) => el.textContent);
    expect(filenameCells[0]).toBe("alpha.csv");
  });

  it("opens delete confirmation dialog and deletes statement", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "delete-me.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    const deleteSpy = vi
      .spyOn(statementsApi, "deleteStatement")
      .mockResolvedValue(undefined);

    render(<AppStatementsPage />);

    await screen.findAllByText("delete-me.csv");

    fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    expect(
      await screen.findByRole("heading", { name: "Delete Statement" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Delete"));

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith("1");
    });

    expect(screen.queryAllByText("delete-me.csv")).toHaveLength(0);
  });

  it("renders empty state when no statements", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);

    render(<AppStatementsPage />);

    expect(await screen.findByText("No Statements Yet")).toBeInTheDocument();
  });
});
