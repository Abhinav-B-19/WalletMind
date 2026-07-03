import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { AppStatementUploadPage } from "@/pages/app-statement-upload-page";
import * as statementsApi from "@/lib/api/statements";

const navigateMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );

  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

function createFile(name: string): File {
  return new File(["date,description,amount\n2026-01-01,Coffee,-4.5"], name, {
    type: "text/csv",
  });
}

describe("AppStatementUploadPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    navigateMock.mockReset();
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

  it("opens success dialog with metadata and truncation tooltip after upload", async () => {
    const longName =
      "bank-statement-super-long-file-name-for-ellipsis-and-tooltip-validation-2026-07.csv";

    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);
    vi.spyOn(statementsApi, "uploadStatement").mockResolvedValue({
      statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f450",
      stored_file_path: "/tmp/stored.csv",
      original_filename: longName,
      stored_filename: "stored.csv",
      file_size: 77,
      file_type: "csv",
      parser_type: "csv",
      bank_name: null,
      classification_confidence: 0.82,
      classification_method: "header-keyword",
      classified_at: "2026-07-03T09:00:01.000Z",
      parsed_transaction_count: 0,
      failed_transaction_count: 0,
      analysis_status: "ready_for_parsing",
      status: "ready_for_parsing",
      uploaded_at: "2026-07-03T09:00:00.000Z",
    });

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [createFile(longName)] } });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    expect(
      await screen.findByRole("heading", {
        name: "Statement Uploaded Successfully",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Your statement has been securely uploaded and is ready for AI analysis.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Filename")).toBeInTheDocument();
    expect(screen.getByText("File Size")).toBeInTheDocument();
    expect(screen.getByText("Parser Type")).toBeInTheDocument();
    expect(screen.getByText("Upload Time")).toBeInTheDocument();
    expect(screen.getByText("Analysis Status")).toBeInTheDocument();
    expect(screen.getByText("Ready for Analysis")).toBeInTheDocument();

    const filenameElement = screen.getByLabelText(`Full filename: ${longName}`);
    expect(filenameElement).toHaveAttribute("title", longName);
    expect(filenameElement.className).toContain("truncate");
  });

  it("Upload Another resets upload page state", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);
    vi.spyOn(statementsApi, "uploadStatement").mockResolvedValue({
      statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f451",
      stored_file_path: "/tmp/stored.csv",
      original_filename: "statement.csv",
      stored_filename: "stored.csv",
      file_size: 77,
      file_type: "csv",
      parser_type: "csv",
      bank_name: null,
      classification_confidence: 0.82,
      classification_method: "header-keyword",
      classified_at: "2026-07-03T09:00:01.000Z",
      parsed_transaction_count: 0,
      failed_transaction_count: 0,
      analysis_status: "ready_for_parsing",
      status: "ready_for_parsing",
      uploaded_at: "2026-07-03T09:00:00.000Z",
    });

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, {
      target: { files: [createFile("statement.csv")] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    await screen.findByRole("heading", {
      name: "Statement Uploaded Successfully",
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Another" }));

    await waitFor(() => {
      expect(
        screen.queryByRole("heading", {
          name: "Statement Uploaded Successfully",
        }),
      ).not.toBeInTheDocument();
    });

    expect(screen.queryByText("statement.csv")).not.toBeInTheDocument();
  });

  it("View Statement Library navigates correctly", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);
    vi.spyOn(statementsApi, "uploadStatement").mockResolvedValue({
      statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f452",
      stored_file_path: "/tmp/stored.csv",
      original_filename: "statement.csv",
      stored_filename: "stored.csv",
      file_size: 77,
      file_type: "csv",
      parser_type: "csv",
      bank_name: null,
      classification_confidence: 0.82,
      classification_method: "header-keyword",
      classified_at: "2026-07-03T09:00:01.000Z",
      parsed_transaction_count: 0,
      failed_transaction_count: 0,
      analysis_status: "ready_for_parsing",
      status: "ready_for_parsing",
      uploaded_at: "2026-07-03T09:00:00.000Z",
    });

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, {
      target: { files: [createFile("statement.csv")] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    await screen.findByRole("heading", {
      name: "Statement Uploaded Successfully",
    });

    fireEvent.click(
      screen.getByRole("button", { name: "View Statement Library" }),
    );

    expect(navigateMock).toHaveBeenCalledWith("/app/statements", {
      state: expect.objectContaining({ refreshToken: expect.any(Number) }),
    });
  });

  it("shows duplicate warning and Cancel aborts upload", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f453",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "statement.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.82,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "ready_for_parsing",
        status: "ready_for_parsing",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      },
    ]);
    const uploadSpy = vi
      .spyOn(statementsApi, "uploadStatement")
      .mockResolvedValue({
        statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f454",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "statement.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.82,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "ready_for_parsing",
        status: "ready_for_parsing",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      });

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, {
      target: { files: [createFile("statement.csv")] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    expect(
      await screen.findByRole("heading", {
        name: "Duplicate Statement Detected",
      }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: "Duplicate Statement Detected" }),
      ).not.toBeInTheDocument();
    });

    expect(uploadSpy).not.toHaveBeenCalled();
  });

  it("Upload Anyway continues upload after duplicate warning", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([
      {
        statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f455",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "statement.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.82,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "ready_for_parsing",
        status: "ready_for_parsing",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      },
    ]);
    const uploadSpy = vi
      .spyOn(statementsApi, "uploadStatement")
      .mockResolvedValue({
        statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f456",
        stored_file_path: "/tmp/stored.csv",
        original_filename: "statement.csv",
        stored_filename: "stored.csv",
        file_size: 77,
        file_type: "csv",
        parser_type: "csv",
        bank_name: null,
        classification_confidence: 0.82,
        classification_method: "header-keyword",
        classified_at: "2026-07-03T09:00:01.000Z",
        parsed_transaction_count: 0,
        failed_transaction_count: 0,
        analysis_status: "ready_for_parsing",
        status: "ready_for_parsing",
        uploaded_at: "2026-07-03T09:00:00.000Z",
      });

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, {
      target: { files: [createFile("statement.csv")] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    await screen.findByRole("heading", {
      name: "Duplicate Statement Detected",
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload Anyway" }));

    await screen.findByRole("heading", {
      name: "Statement Uploaded Successfully",
    });
    expect(uploadSpy).toHaveBeenCalledTimes(1);
  });

  it("accepts current backend upload payload with queued status without validation error", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);
    vi.spyOn(statementsApi, "uploadStatement").mockResolvedValue({
      statement_uuid: "a4b7a8e2-9d50-4c9d-8f6c-53f2d6a8f457",
      stored_file_path: "/tmp/stored.csv",
      original_filename: "pipeline.csv",
      stored_filename: "stored.csv",
      file_size: 77,
      file_type: "csv",
      parser_type: "csv",
      bank_name: null,
      classification_confidence: 0.82,
      classification_method: "header-keyword",
      classified_at: "2026-07-03T09:00:01.000Z",
      parsed_transaction_count: 0,
      failed_transaction_count: 0,
      analysis_status: "ready_for_parsing",
      status: "ready_for_parsing",
      uploaded_at: "2026-07-03T09:00:00.000Z",
    });

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, {
      target: { files: [createFile("pipeline.csv")] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    expect(
      await screen.findByRole("heading", {
        name: "Statement Uploaded Successfully",
      }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Upload validation")).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "Received an unexpected response from the upload service.",
      ),
    ).not.toBeInTheDocument();
  });

  it("shows upload validation when upload service returns error", async () => {
    vi.spyOn(statementsApi, "listStatements").mockResolvedValue([]);
    vi.spyOn(statementsApi, "uploadStatement").mockRejectedValue(
      new Error("Upload service is temporarily unavailable. Please try again."),
    );

    render(<AppStatementUploadPage />);

    const fileInput = document.querySelector(
      "input[type='file']",
    ) as HTMLInputElement;
    fireEvent.change(fileInput, {
      target: { files: [createFile("pipeline.csv")] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Statement" }));

    expect(await screen.findByText("Upload validation")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Upload service is temporarily unavailable. Please try again.",
      ),
    ).toBeInTheDocument();
  });
});
