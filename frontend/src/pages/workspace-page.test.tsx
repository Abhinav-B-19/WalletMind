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
        original_filename: "salary-june.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        analysis_status: "queued",
        status: "queued",
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
    expect(screen.getByText("1 total statement in your library.")).toBeInTheDocument();
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

  it("shows ready_for_parsing statements in Ready For Analysis", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        original_filename: "pipeline.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
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

    const matchingFilenames = await screen.findAllByText("pipeline.csv");
    expect(matchingFilenames.length).toBeGreaterThan(0);
    expect(screen.getByText("Ready For Parsing")).toBeInTheDocument();
  });

  it("handles future processing states in Ready For Analysis", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        original_filename: "future-state.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
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
    expect(screen.getByText("Analysis Pending")).toBeInTheDocument();
    expect(
      screen.queryByText("Nothing queued for AI analysis"),
    ).not.toBeInTheDocument();
  });

  it("renders basic profile cards and preserves integration after refresh-like remount", async () => {
    const listSpy = vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        original_filename: "refresh.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        analysis_status: "queued",
        status: "queued",
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
