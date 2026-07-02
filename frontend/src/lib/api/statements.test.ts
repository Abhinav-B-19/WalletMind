import { describe, expect, it, vi, beforeEach } from "vitest";

import { listStatements, uploadStatement } from "@/lib/api/statements";
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
          original_filename: "statement.csv",
          stored_filename: "stored.csv",
          file_size: 77,
          file_type: "csv",
          parser_type: "csv",
          bank_name: null,
          analysis_status: "queued",
          status: "queued",
          uploaded_at: "2026-07-03T09:00:00.000Z",
        },
      },
    });

    const result = await uploadStatement({
      userUuid: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
      file: new File(["a,b\n1,2"], "statement.csv", { type: "text/csv" }),
    });

    expect(result.statement_uuid).toBe("8fe70b89-2325-42b6-82a6-16c6268d56eb");
    expect(result.status).toBe("queued");
    expect(result.analysis_status).toBe("queued");
    expect(result.parser_type).toBe("csv");
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
            original_filename: "statement.csv",
            stored_filename: "stored.csv",
            file_size: 77,
            file_type: "csv",
            parser_type: "csv",
            bank_name: null,
            analysis_status: "ready_for_parsing",
            status: "ready_for_parsing",
            uploaded_at: "2026-07-03T09:00:00.000Z",
          },
        ],
      },
    });

    const statements = await listStatements("f7ed2559-7ec3-4433-b9e4-af8ca6adf72b");

    expect(statements).toHaveLength(1);
    expect(statements[0]?.status).toBe("ready_for_parsing");
    expect(statements[0]?.parser_type).toBe("csv");
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
    ).rejects.toThrow("Received an unexpected response from the upload service.");
  });

  it("maps transport failures to user-friendly upload error", async () => {
    const postMock = vi.mocked(apiClient.post);
    postMock.mockRejectedValue(new Error("network down"));

    await expect(
      uploadStatement({
        userUuid: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        file: new File(["a,b\n1,2"], "statement.csv", { type: "text/csv" }),
      }),
    ).rejects.toThrow("Unable to upload statement right now. Please try again.");
  });
});
