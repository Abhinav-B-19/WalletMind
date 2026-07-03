import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, beforeEach, vi } from "vitest";

import { WorkspacePage } from "@/pages/workspace-page";
import * as statementsApi from "@/lib/api/statements";

describe("WorkspacePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
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
  });

  it("renders uploaded statements in Home Recent Statements", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "salary-june.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.88,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "ready_for_parsing",
        status: "ready_for_parsing",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      },
    ]);

    render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    const matchingFilenames = await screen.findAllByText("salary-june.csv");
    expect(matchingFilenames.length).toBeGreaterThan(0);
    expect(
      screen.queryByText("No statements in your library yet"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("1 total statement in your library."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open Statement Library" }),
    ).toBeInTheDocument();
  });

  it("shows empty state only when API returns zero statements", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);

    render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("No statements in your library yet"),
    ).toBeInTheDocument();
  });

  it("shows ready_for_analysis statements in Ready For Analysis", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "pipeline.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.88,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "ready_for_analysis",
        status: "ready_for_analysis",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      },
    ]);

    render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    const matchingFilenames = await screen.findAllByText("pipeline.csv");
    expect(matchingFilenames.length).toBeGreaterThan(0);
    expect(screen.getAllByText("Ready For Analysis").length).toBeGreaterThan(0);
  });

  it("does not include non-ready states in Ready For Analysis", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "future-state.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.7,
        classification_method: "metadata",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "analysis_pending",
        status: "analysis_pending",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      },
    ]);

    render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    const matchingFilenames = await screen.findAllByText("future-state.csv");
    expect(matchingFilenames.length).toBeGreaterThan(0);
    expect(
      screen.getByText("Nothing queued for AI analysis"),
    ).toBeInTheDocument();
  });

  it("renders basic profile cards and preserves integration after refresh-like remount", async () => {
    const listSpy = vi
      .spyOn(statementsApi, "listStatements")
      .mockResolvedValue([
        {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          stored_file_path: "/tmp/stored.csv",
          original_filename: "refresh.csv",
          stored_filename: "stored.csv",
          file_size: 77,
          file_type: "csv",
          parser_type: "csv",
          bank_name: null,
          classification_confidence: 0.88,
          classification_method: "header-keyword",
          classified_at: "2026-07-03T09:00:01.000Z",
          parsed_transaction_count: 0,
          failed_transaction_count: 0,
          analysis_status: "ready_for_parsing",
          status: "ready_for_parsing",
          uploaded_at: "2026-07-03T09:00:00.000Z",
        },
      ]);

    const { unmount } = render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    const firstPassMatches = await screen.findAllByText("refresh.csv");
    expect(firstPassMatches.length).toBeGreaterThan(0);
    expect(screen.getByText("INR")).toBeInTheDocument();
    expect(screen.getByText("Build Emergency Fund")).toBeInTheDocument();

    unmount();

    render(
      <MemoryRouter>
        <WorkspacePage />
      </MemoryRouter>,
    );

    const secondPassMatches = await screen.findAllByText("refresh.csv");
    expect(secondPassMatches.length).toBeGreaterThan(0);
    await waitFor(() => {
      expect(listSpy).toHaveBeenCalledTimes(2);
    });
  });
});
