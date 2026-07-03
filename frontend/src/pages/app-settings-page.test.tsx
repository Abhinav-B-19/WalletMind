import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppSettingsPage } from "@/pages/app-settings-page";
import * as statementsApi from "@/lib/api/statements";
import {
  useAIHealth,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";

vi.mock("@/features/ai-dashboard/hooks", () => ({
  useAIHealth: vi.fn(),
  useProcessedStatements: vi.fn(),
}));

vi.mock("@/lib/auth/storage", () => ({
  getStoredUser: () => ({
    id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
    name: "Priya",
    occupation: "Engineer",
    monthly_income: 120000,
    currency: "INR",
    primary_financial_goal: "Build Emergency Fund",
  }),
}));

function createWrapper(initialPath = "/app/settings") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("AppSettingsPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.mocked(useProcessedStatements).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [
        {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          stored_file_path: "/tmp/stored.csv",
          original_filename: "statement.csv",
          stored_filename: "stored.csv",
          file_size: 100,
          file_type: "csv",
          parser_type: "csv",
          bank_name: null,
          classification_confidence: 0.9,
          classification_method: "header-keyword",
          classified_at: "2026-07-03T09:00:01.000Z",
          parsed_transaction_count: 5,
          failed_transaction_count: 0,
          parsed_at: "2026-07-03T09:00:02.000Z",
          analysis_status: "ready_for_analysis",
          status: "ready_for_analysis",
          uploaded_at: "2026-07-03T09:00:00.000Z",
        },
      ],
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProcessedStatements>);

    vi.mocked(useAIHealth).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: {
        configured: true,
        model: "gemini-2.5-flash",
        status: "healthy",
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useAIHealth>);

    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "statement.csv",
        stored_filename: "stored.csv",
        file_size: 4096,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.9,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 12,
        failed_transaction_count: 0,
        parsed_at: "2026-07-03T09:00:02.000Z",
        analysis_status: "ready_for_analysis",
        status: "ready_for_analysis",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      },
    ]);
  });

  it("renders all major settings sections", async () => {
    render(<AppSettingsPage />, { wrapper: createWrapper() });

    expect(
      await screen.findByRole("heading", { name: "Settings", level: 2 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Application")).toBeInTheDocument();
    expect(screen.getByText("AI Configuration")).toBeInTheDocument();
    expect(screen.getByText("Data Management")).toBeInTheDocument();
    expect(screen.getByText("Privacy & Security")).toBeInTheDocument();
    expect(screen.getByText("Application Features")).toBeInTheDocument();
    expect(screen.getByText("System Information")).toBeInTheDocument();
    expect(screen.getByText("About")).toBeInTheDocument();
  });

  it("shows healthy status cards when AI health and backend data are available", async () => {
    render(<AppSettingsPage />, { wrapper: createWrapper() });

    expect((await screen.findAllByText("Connected")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Healthy").length).toBeGreaterThan(0);
  });

  it("renders responsive grid classes and read-only fields", async () => {
    render(<AppSettingsPage />, { wrapper: createWrapper() });

    const settingsGrid = await screen.findByTestId("settings-grid");
    expect(settingsGrid).toHaveClass("md:grid-cols-2");
    expect(settingsGrid).toHaveClass("xl:grid-cols-3");

    const fields = screen.getAllByTestId("settings-readonly-field");
    expect(fields.length).toBeGreaterThan(4);
    fields.forEach((field) => {
      expect(field).toHaveAttribute("aria-readonly", "true");
    });
  });

  it("shows warning health status when AI service reports unhealthy", async () => {
    vi.mocked(useAIHealth).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: {
        configured: true,
        model: "gemini-2.5-flash",
        status: "unhealthy",
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useAIHealth>);

    render(<AppSettingsPage />, { wrapper: createWrapper() });

    expect(await screen.findAllByText("Unhealthy")).toHaveLength(2);
  });
});
