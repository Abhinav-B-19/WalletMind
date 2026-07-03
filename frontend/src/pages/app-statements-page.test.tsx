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
  overrides: Partial<{
    parser_type: string;
    bank_name: string | null;
  }> = {},
) {
  const bankName = Object.prototype.hasOwnProperty.call(overrides, "bank_name")
    ? overrides.bank_name
    : "Demo Bank";

  return {
    statement_uuid,
    stored_file_path: `/tmp/${statement_uuid}.csv`,
    original_filename,
    stored_filename: `${statement_uuid}.csv`,
    file_size,
    file_type: "csv",
    parser_type: overrides.parser_type ?? "csv_parser",
    bank_name: bankName,
    classification_confidence: 0.88,
    classification_method: "header-keyword",
    classified_at: "2026-07-03T09:00:01.000Z",
    parsed_transaction_count: 1,
    failed_transaction_count: 0,
    parsed_at: "2026-07-03T09:00:02.000Z",
    direction_corrections: 2,
    analysis_status: "ready_for_analysis" as const,
    status: "ready_for_analysis" as const,
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
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

    render(<AppStatementsPage />);

    expect(await screen.findAllByText("alpha.csv")).toHaveLength(2);
    expect(screen.getAllByText("beta.csv")).toHaveLength(2);
  });

  it("filters statements by instant search", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "salary.csv", "2026-07-03T10:00:00.000Z"),
      makeStatement("2", "groceries.csv", "2026-07-02T10:00:00.000Z"),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

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
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

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
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);
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
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

    render(<AppStatementsPage />);

    expect(await screen.findByText("No Statements Yet")).toBeInTheDocument();
  });

  it("loads statement transactions when View Details is clicked", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    const txSpy = vi
      .spyOn(statementsApi, "getStatementTransactions")
      .mockResolvedValue([
        {
          transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56ea",
          statement_uuid: "1",
          transaction_date: "2026-07-01",
          description: "Salary",
          debit: null,
          credit: 1000,
          amount: 1000,
          transaction_type: "credit",
          balance: 1200,
          currency: "USD",
          reference_number: null,
          merchant_name: "Employer Payroll",
          bank_gateway: null,
          category: "Income",
          raw_description: "Salary",
          clean_description: "salary",
          normalized_transaction_type: "income",
          flags: {
            is_internal_transfer: false,
            is_income: true,
            is_expense: false,
          },
          raw_row_json: {},
          created_at: "2026-07-01T10:00:00.000Z",
        },
      ]);

    render(<AppStatementsPage />);

    await screen.findAllByText("alpha.csv");
    fireEvent.click(screen.getAllByRole("button", { name: "View Details" })[0]);

    await waitFor(() => {
      expect(txSpy).toHaveBeenCalledWith("1");
    });
    expect(await screen.findByText("Employer Payroll")).toBeInTheDocument();
    expect(screen.getAllByText("Income").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
    expect(screen.getByText("Demo Bank • csv_parser")).toBeInTheDocument();
  });

  it("filters and searches enriched transactions inside modal", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([
      {
        transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56ea",
        statement_uuid: "1",
        transaction_date: "2026-07-01",
        description: "UPI/P2M/GROWW SIP",
        debit: -500,
        credit: null,
        amount: -500,
        transaction_type: "debit",
        balance: 1000,
        currency: "INR",
        reference_number: null,
        merchant_name: "GROWW SIP",
        bank_gateway: null,
        category: "Investments",
        raw_description: "UPI/P2M/GROWW SIP",
        clean_description: "groww sip",
        normalized_transaction_type: "expense",
        flags: {
          is_internal_transfer: false,
          is_income: false,
          is_expense: true,
        },
        raw_row_json: {},
        created_at: "2026-07-01T10:00:00.000Z",
      },
      {
        transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        statement_uuid: "1",
        transaction_date: "2026-07-02",
        description: "UPI/P2M/BP Petrol Pump",
        debit: -200,
        credit: null,
        amount: -200,
        transaction_type: "debit",
        balance: 800,
        currency: "INR",
        reference_number: null,
        merchant_name: "BP Petrol Pump",
        bank_gateway: "YES BANK LIMITED",
        category: "Fuel",
        raw_description: "UPI/P2M/BP Petrol Pump",
        clean_description: "bp petrol pump",
        normalized_transaction_type: "expense",
        flags: {
          is_internal_transfer: false,
          is_income: false,
          is_expense: true,
        },
        raw_row_json: {},
        created_at: "2026-07-02T10:00:00.000Z",
      },
    ]);

    render(<AppStatementsPage />);

    await screen.findAllByText("alpha.csv");
    fireEvent.click(screen.getAllByRole("button", { name: "View Details" })[0]);

    await screen.findByText("GROWW SIP");
    expect(screen.getAllByText("Investments").length).toBeGreaterThan(0);
    expect(screen.getAllByText("expense").length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("Search transactions"), {
      target: { value: "groww" },
    });
    expect(screen.getByText("GROWW SIP")).toBeInTheDocument();
    expect(screen.queryByText("BP Petrol Pump")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search transactions"), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("Filter transactions by category"), {
      target: { value: "Fuel" },
    });
    expect(screen.getByText("BP Petrol Pump")).toBeInTheDocument();
    expect(screen.queryByText("GROWW SIP")).not.toBeInTheDocument();
  });

  it("opens transaction details modal and shows original narration", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([
      {
        transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56ea",
        statement_uuid: "1",
        transaction_date: "2026-07-01",
        description:
          "UPI/P2M/617688132790/GROWW INVEST TECH PVT/Paid V/HDFC BANK LTD",
        debit: -500,
        credit: null,
        amount: -500,
        transaction_type: "debit",
        balance: 1000,
        currency: "INR",
        reference_number: "617688132790",
        merchant_name: "GROWW INVEST TECH PVT",
        bank_gateway: "HDFC BANK LTD",
        category: "Investments",
        raw_description:
          "UPI/P2M/617688132790/GROWW INVEST TECH PVT/Paid V/HDFC BANK LTD",
        clean_description: "groww invest tech pvt",
        normalized_transaction_type: "expense",
        flags: {
          is_internal_transfer: false,
          is_income: false,
          is_expense: true,
        },
        raw_row_json: {},
        created_at: "2026-07-01T10:00:00.000Z",
      },
    ]);

    render(<AppStatementsPage />);

    await screen.findAllByText("alpha.csv");
    fireEvent.click(screen.getAllByRole("button", { name: "View Details" })[0]);

    await screen.findByText("GROWW INVEST TECH PVT");
    fireEvent.click(screen.getByLabelText("Open transaction details"));

    expect(await screen.findByText("Transaction Details")).toBeInTheDocument();
    expect(screen.getByText("Description:")).toBeInTheDocument();
    expect(screen.getByText("Merchant:")).toBeInTheDocument();
    expect(screen.getByText("Bank / Gateway:")).toBeInTheDocument();
    expect(screen.getByText("HDFC BANK LTD")).toBeInTheDocument();
    expect(screen.getByText("Original Bank Narration")).toBeInTheDocument();
    expect(
      screen.getByText(
        "UPI/P2M/617688132790/GROWW INVEST TECH PVT/Paid V/HDFC BANK LTD",
      ),
    ).toBeInTheDocument();
  });

  it("shows parser summary direction corrections", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

    render(<AppStatementsPage />);

    await screen.findAllByText("alpha.csv");
    fireEvent.click(screen.getAllByRole("button", { name: "View Details" })[0]);

    expect(
      await screen.findByText("Direction Corrections:"),
    ).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders description and merchant columns in required order", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([
      {
        transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56ec",
        statement_uuid: "1",
        transaction_date: "2026-07-01",
        description:
          "UPI/P2M/654547230671/MUNIYANDI C /haircu/YES BANK LIMITED YBS",
        debit: -99,
        credit: null,
        amount: -99,
        transaction_type: "debit",
        balance: 1000,
        currency: "INR",
        reference_number: "654547230671",
        merchant_name: "MUNIYANDI C",
        bank_gateway: "YES BANK LIMITED YBS",
        category: "Personal Care",
        raw_description:
          "UPI/P2M/654547230671/MUNIYANDI C /haircu/YES BANK LIMITED YBS",
        clean_description: "Haircut",
        normalized_transaction_type: "expense",
        flags: {
          is_internal_transfer: false,
          is_income: false,
          is_expense: true,
        },
        raw_row_json: {},
        created_at: "2026-07-01T10:00:00.000Z",
      },
    ]);

    render(<AppStatementsPage />);

    await screen.findAllByText("alpha.csv");
    fireEvent.click(screen.getAllByRole("button", { name: "View Details" })[0]);

    const descriptionHeader = await screen.findByRole("columnheader", {
      name: "Description",
    });
    const merchantHeader = screen.getByRole("columnheader", {
      name: "Merchant",
    });
    expect(descriptionHeader).toBeInTheDocument();
    expect(merchantHeader).toBeInTheDocument();
    expect(screen.getByText("Haircut")).toBeInTheDocument();
    expect(screen.getByText("MUNIYANDI C")).toBeInTheDocument();
  });

  it("closes details modal with Close button", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "alpha.csv", "2026-07-03T10:00:00.000Z"),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

    render(<AppStatementsPage />);

    await screen.findAllByText("alpha.csv");
    fireEvent.click(screen.getAllByRole("button", { name: "View Details" })[0]);
    expect(
      await screen.findByRole("button", { name: "Close" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: "Close" }),
      ).not.toBeInTheDocument();
    });
  });

  it("shows Unknown when bank detection fails", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      makeStatement("1", "mystery.csv", "2026-07-03T10:00:00.000Z", 77, {
        bank_name: null,
      }),
    ]);
    vi.spyOn(statementsApi, "getStatementTransactions").mockResolvedValue([]);

    render(<AppStatementsPage />);

    const unknowns = await screen.findAllByText("Unknown");
    expect(unknowns.length).toBeGreaterThan(0);
  });
});
