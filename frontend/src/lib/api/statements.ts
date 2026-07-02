import axios from "axios";
import { z } from "zod";

import { apiClient } from "@/lib/api/client";

const statementStatusSchema = z.enum([
  "uploaded",
  "queued",
  "processing",
  "ready_for_parsing",
  "parsed",
  "analysis_pending",
  "completed",
  "failed",
]);

const uploadDataSchema = z.object({
  statement_uuid: z.string().uuid(),
  original_filename: z.string(),
  stored_filename: z.string(),
  file_size: z.number(),
  file_type: z.string(),
  parser_type: z.string(),
  bank_name: z.string().nullable().optional(),
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
