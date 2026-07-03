import axios from "axios";
import { z } from "zod";

import { apiClient } from "@/lib/api/client";

const decimalFieldSchema = z
  .union([z.number(), z.string()])
  .transform((value, context) => {
    if (typeof value === "number") {
      return value;
    }

    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Invalid decimal value: ${value}`,
      });
      return z.NEVER;
    }

    return parsed;
  });

const statementStatusSchema = z.enum([
  "queued",
  "uploaded",
  "classifying",
  "classified",
  "processing",
  "ready_for_parsing",
  "parsed",
  "analysis_pending",
  "ready_for_analysis",
  "parse_failed",
  "completed",
  "failed",
]);

const transactionDataSchema = z.object({
  transaction_uuid: z.string().uuid(),
  statement_uuid: z.string().uuid(),
  transaction_date: z.string(),
  description: z.string(),
  debit: decimalFieldSchema.nullable().optional(),
  credit: decimalFieldSchema.nullable().optional(),
  amount: decimalFieldSchema,
  transaction_type: z.string(),
  balance: decimalFieldSchema.nullable().optional(),
  currency: z.string().nullable().optional(),
  reference_number: z.string().nullable().optional(),
  merchant_name: z.string().nullable().optional(),
  bank_gateway: z.string().nullable().optional(),
  category: z.string(),
  subcategory: z.string().nullable().optional(),
  payment_channel: z.string(),
  transaction_kind: z.string(),
  confidence_score: z.number().int().nonnegative(),
  raw_description: z.string(),
  clean_description: z.string(),
  normalized_transaction_type: z.string(),
  flags: z
    .object({
      is_transfer: z.boolean(),
      is_internal_transfer: z.boolean(),
      is_subscription: z.boolean(),
      is_recurring: z.boolean(),
      is_salary: z.boolean(),
      is_cash: z.boolean(),
      is_atm: z.boolean(),
      is_loan: z.boolean(),
      is_investment: z.boolean(),
      is_tax: z.boolean(),
      is_income: z.boolean(),
      is_expense: z.boolean(),
    })
    .optional(),
  raw_row_json: z.record(z.string(), z.unknown()),
  created_at: z.string(),
});

const uploadDataSchema = z.object({
  statement_uuid: z.string().uuid(),
  stored_file_path: z.string().optional(),
  original_filename: z.string(),
  stored_filename: z.string(),
  file_size: z.number(),
  file_type: z.string(),
  parser_type: z.string(),
  bank_name: z.string().nullable().optional(),
  classification_confidence: z.number().nullable().optional(),
  classification_method: z.string().nullable().optional(),
  classified_at: z.string().nullable().optional(),
  parsed_transaction_count: z.number().int().nonnegative().default(0),
  failed_transaction_count: z.number().int().nonnegative().default(0),
  parsed_at: z.string().nullable().optional(),
  rows_read: z.number().int().nonnegative().optional(),
  rows_parsed: z.number().int().nonnegative().optional(),
  rows_skipped: z.number().int().nonnegative().optional(),
  direction_corrections: z.number().int().nonnegative().optional(),
  parsing_duration_ms: z.number().int().nonnegative().optional(),
  analysis_status: statementStatusSchema,
  status: statementStatusSchema,
  uploaded_at: z.string(),
});

const uploadEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: uploadDataSchema,
});

const listEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: z.array(uploadDataSchema),
});

const transactionListEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: z.array(transactionDataSchema),
});

const deleteEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: z
    .object({
      statement_uuid: z.string().uuid().optional(),
    })
    .optional(),
});

export type UploadedStatement = z.infer<typeof uploadDataSchema>;
export type TransactionRecord = z.infer<typeof transactionDataSchema>;

type UploadStatementInput = {
  userUuid: string;
  file: File;
  onUploadProgress?: (progressPercentage: number) => void;
};

function toFriendlyUploadError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;

    if (!error.response) {
      return new Error(
        "Upload service is currently unreachable. Please try again shortly.",
      );
    }

    if (status === 413) {
      return new Error("File is too large. Please upload a smaller file.");
    }

    if (status === 415) {
      return new Error(
        "Unsupported file type. Please choose a supported format.",
      );
    }

    if (status === 422 || status === 400) {
      return new Error(
        "We could not process that file. Please verify and try again.",
      );
    }

    if (status && status >= 500) {
      return new Error(
        "Upload service is temporarily unavailable. Please try again.",
      );
    }

    return new Error("Unable to upload statement right now. Please try again.");
  }

  if (error instanceof z.ZodError) {
    return new Error(
      "Received an unexpected response from the upload service.",
    );
  }

  if (error instanceof Error) {
    return new Error("Unable to upload statement right now. Please try again.");
  }

  return new Error("Unable to upload statement right now. Please try again.");
}

export async function uploadStatement({
  userUuid,
  file,
  onUploadProgress,
}: UploadStatementInput): Promise<UploadedStatement> {
  const formData = new FormData();
  formData.append("user_uuid", userUuid);
  formData.append("file", file);

  try {
    const response = await apiClient.post("/statements/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (event) => {
        if (!onUploadProgress || !event.total) {
          return;
        }

        const progressPercentage = Math.min(
          100,
          Math.round((event.loaded * 100) / event.total),
        );
        onUploadProgress(progressPercentage);
      },
    });

    const parsed = uploadEnvelopeSchema.parse(response.data);
    return parsed.data;
  } catch (error) {
    throw toFriendlyUploadError(error);
  }
}

export async function listStatements(
  userUuid?: string,
): Promise<UploadedStatement[]> {
  try {
    const response = await apiClient.get("/statements", {
      params: userUuid ? { user_uuid: userUuid } : undefined,
    });

    const parsed = listEnvelopeSchema.parse(response.data);
    return parsed.data;
  } catch (error) {
    throw toFriendlyUploadError(error);
  }
}

export async function deleteStatement(statementUuid: string): Promise<void> {
  try {
    const response = await apiClient.delete(`/statements/${statementUuid}`);
    deleteEnvelopeSchema.parse(response.data);
  } catch (error) {
    throw toFriendlyUploadError(error);
  }
}

export async function getStatementTransactions(
  statementUuid: string,
): Promise<TransactionRecord[]> {
  const requestUrl = `/statements/${statementUuid}/transactions`;

  console.info("[transactions] request:start", {
    requestUrl,
    statementUuid,
  });

  try {
    const response = await apiClient.get(requestUrl);
    console.info("[transactions] request:response", {
      requestUrl,
      status: response.status,
      payload: response.data,
    });

    const parsed = transactionListEnvelopeSchema.parse(response.data);
    console.info("[transactions] request:validated", {
      statementUuid,
      transactionCount: parsed.data.length,
    });

    return parsed.data;
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstIssue = error.issues[0];
      const issuePath =
        firstIssue?.path?.length && firstIssue.path.length > 0
          ? firstIssue.path.join(".")
          : "unknown";
      const issueCode = firstIssue?.code ?? "unknown";
      const payloadKeys =
        typeof (error as unknown) === "object" && error !== null
          ? Object.keys((error as { input?: unknown }).input ?? {})
          : [];

      console.error("[transactions] schema:validation_failed", {
        statementUuid,
        issues: error.issues,
        failingField: issuePath,
        issueCode,
        payloadKeys,
      });
      throw new Error(
        `Transaction response validation failed at ${issuePath}: ${firstIssue?.message ?? "Unknown schema mismatch"}`,
      );
    }

    if (error instanceof Error) {
      console.error("[transactions] request:error", {
        statementUuid,
        message: error.message,
      });
      throw error;
    }

    throw toFriendlyUploadError(error);
  }
}
