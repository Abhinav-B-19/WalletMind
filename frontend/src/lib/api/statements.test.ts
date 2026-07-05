import { describe, expect, it, vi, beforeEach } from "vitest";

import {
  getStatementTransactions,
  listStatements,
  uploadStatement,
} from "@/lib/api/statements";
import { apiClient } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("statements api contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("parses current upload response contract with queued status", async () => {
    const postMock = vi.mocked(apiClient.post);
    postMock.mockResolvedValue({
      data: {
        success: true,
        message: "Statement uploaded successfully.",
        data: {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          stored_file_path: "/tmp/stored.csv",
          original_filename: "statement.csv",
          stored_filename: "stored.csv",
          file_size: 77,
          file_type: "csv",
          parser_type: "csv",
          bank_name: null,
          classification_confidence: 0.88,
          classification_method: "header-keyword",
          classified_at: "2026-07-03T09:00:01.000Z",
          parsed_transaction_count: 1,
          failed_transaction_count: 0,
          parsed_at: "2026-07-03T09:00:02.000Z",
          direction_corrections: 2,
          analysis_status: "ready_for_analysis",
          status: "ready_for_analysis",
          uploaded_at: "2026-07-03T09:00:00.000Z",
        },
      },
    });

    const result = await uploadStatement({
      userUuid: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
      file: new File(["a,b\n1,2"], "statement.csv", { type: "text/csv" }),
    });

    expect(result.statement_uuid).toBe("8fe70b89-2325-42b6-82a6-16c6268d56eb");
    expect(result.status).toBe("ready_for_analysis");
    expect(result.analysis_status).toBe("ready_for_analysis");
    expect(result.parser_type).toBe("csv");
    expect(result.parsed_transaction_count).toBe(1);
  });

  it("accepts list payload containing ready_for_parsing status", async () => {
    const getMock = vi.mocked(apiClient.get);
    getMock.mockResolvedValue({
      data: {
        success: true,
        message: "Statements retrieved successfully.",
        data: [
          {
            statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
            stored_file_path: "/tmp/stored.csv",
            original_filename: "statement.csv",
            stored_filename: "stored.csv",
            file_size: 77,
            file_type: "csv",
            parser_type: "csv",
            bank_name: null,
            classification_confidence: 0.88,
            classification_method: "header-keyword",
            classified_at: "2026-07-03T09:00:01.000Z",
            parsed_transaction_count: 2,
            failed_transaction_count: 0,
            parsed_at: "2026-07-03T09:00:02.000Z",
            direction_corrections: 1,
            analysis_status: "ready_for_analysis",
            status: "ready_for_analysis",
            uploaded_at: "2026-07-03T09:00:00.000Z",
          },
        ],
      },
    });

    const statements = await listStatements(
      "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
    );

    expect(statements).toHaveLength(1);
    expect(statements[0]?.status).toBe("ready_for_analysis");
    expect(statements[0]?.parser_type).toBe("csv");
  });

  it("parses statement transactions response", async () => {
    const getMock = vi.mocked(apiClient.get);
    getMock.mockResolvedValue({
      data: {
        success: true,
        message: "Statement transactions retrieved successfully.",
        data: [
          {
            transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56ea",
            statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
            transaction_date: "2026-07-03",
            description: "Salary",
            debit: null,
            credit: "1500.00",
            amount: "1500.00",
            transaction_type: "credit",
            balance: "2000.00",
            currency: "USD",
            reference_number: "REF-1",
            merchant_name: "Employer Payroll",
            bank_gateway: null,
            category: "Income",
            subcategory: "Income",
            payment_channel: "Salary Credit",
            transaction_kind: "income",
            confidence_score: 95,
            raw_description: "Salary",
            clean_description: "salary",
            normalized_transaction_type: "income",
            flags: {
              is_transfer: false,
              is_internal_transfer: false,
              is_subscription: false,
              is_recurring: true,
              is_salary: true,
              is_cash: false,
              is_atm: false,
              is_loan: false,
              is_investment: false,
              is_tax: false,
              is_income: true,
              is_expense: false,
            },
            raw_row_json: { row: 1 },
            created_at: "2026-07-03T09:00:03.000Z",
          },
        ],
      },
    });

    const records = await getStatementTransactions(
      "8fe70b89-2325-42b6-82a6-16c6268d56eb",
    );

    expect(records).toHaveLength(1);
    expect(records[0]?.description).toBe("Salary");
    expect(records[0]?.merchant_name).toBe("Employer Payroll");
    expect(records[0]?.bank_gateway).toBeNull();
    expect(records[0]?.category).toBe("Income");
    expect(records[0]?.payment_channel).toBe("Salary Credit");
    expect(records[0]?.confidence_score).toBe(95);
    expect(records[0]?.clean_description).toBe("salary");
    expect(records[0]?.normalized_transaction_type).toBe("income");
    expect(records[0]?.amount).toBe(1500);
    expect(records[0]?.balance).toBe(2000);
  });

  it("throws friendly validation error for malformed backend upload response", async () => {
    const postMock = vi.mocked(apiClient.post);
    postMock.mockResolvedValue({
      data: {
        success: true,
        message: "Statement uploaded successfully.",
        data: {
          id: "legacy-id",
          filename: "legacy.csv",
        },
      },
    });

    await expect(
      uploadStatement({
        userUuid: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        file: new File(["a,b\n1,2"], "statement.csv", { type: "text/csv" }),
      }),
    ).rejects.toThrow(
      "Received an unexpected response from the upload service.",
    );
  });

  it("maps transport failures to user-friendly upload error", async () => {
    const postMock = vi.mocked(apiClient.post);
    postMock.mockRejectedValue(new Error("network down"));

    await expect(
      uploadStatement({
        userUuid: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        file: new File(["a,b\n1,2"], "statement.csv", { type: "text/csv" }),
      }),
    ).rejects.toThrow(
      "Unable to upload statement right now. Please try again.",
    );
  });

  it("sends original File through FormData without overriding multipart headers", async () => {
    const postMock = vi.mocked(apiClient.post);
    postMock.mockResolvedValue({
      data: {
        success: true,
        message: "Statement uploaded successfully.",
        data: {
          statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
          stored_file_path: "/tmp/stored.csv",
          original_filename: "statement.csv",
          stored_filename: "stored.csv",
          file_size: 77,
          file_type: "csv",
          parser_type: "csv",
          bank_name: null,
          classification_confidence: 0.88,
          classification_method: "header-keyword",
          classified_at: "2026-07-03T09:00:01.000Z",
          parsed_transaction_count: 1,
          failed_transaction_count: 0,
          parsed_at: "2026-07-03T09:00:02.000Z",
          direction_corrections: 2,
          analysis_status: "ready_for_analysis",
          status: "ready_for_analysis",
          uploaded_at: "2026-07-03T09:00:00.000Z",
        },
      },
    });

    const file = new File(["a,b\n1,2"], "statement.csv", {
      type: "text/csv",
    });

    await uploadStatement({
      userUuid: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
      file,
    });

    expect(postMock).toHaveBeenCalledTimes(1);
    const [requestUrl, requestBody, requestConfig] =
      postMock.mock.calls[0] ?? [];

    expect(requestUrl).toBe("/statements/upload");
    expect(requestBody).toBeInstanceOf(FormData);

    const formData = requestBody as FormData;
    expect(formData.get("user_uuid")).toBe(
      "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
    );
    expect(formData.get("file")).toBe(file);

    expect(requestConfig).not.toHaveProperty("headers");
  });

  it("reports exact field path when transaction payload mismatches schema", async () => {
    const getMock = vi.mocked(apiClient.get);
    getMock.mockResolvedValue({
      data: {
        success: true,
        message: "Statement transactions retrieved successfully.",
        data: [
          {
            transaction_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56ea",
            statement_uuid: "8fe70b89-2325-42b6-82a6-16c6268d56eb",
            transaction_date: "2026-07-03",
            description: "Salary",
            debit: null,
            credit: "1500.00",
            amount: "1500.00",
            transaction_type: "credit",
            balance: "2000.00",
            currency: "USD",
            reference_number: "REF-1",
            merchant_name: "Employer Payroll",
            bank_gateway: null,
            category: "Income",
            subcategory: "Income",
            transaction_kind: "income",
            confidence_score: 95,
            raw_description: "Salary",
            clean_description: "salary",
            normalized_transaction_type: "income",
            flags: {
              is_transfer: false,
              is_internal_transfer: false,
              is_subscription: false,
              is_recurring: true,
              is_salary: true,
              is_cash: false,
              is_atm: false,
              is_loan: false,
              is_investment: false,
              is_tax: false,
              is_income: true,
              is_expense: false,
            },
            raw_row_json: { row: 1 },
            created_at: "2026-07-03T09:00:03.000Z",
          },
        ],
      },
    });

    await expect(
      getStatementTransactions("8fe70b89-2325-42b6-82a6-16c6268d56eb"),
    ).rejects.toThrow(
      "Transaction response validation failed at data.0.payment_channel",
    );
  });
});
