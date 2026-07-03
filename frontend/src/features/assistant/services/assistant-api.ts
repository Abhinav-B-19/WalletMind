import { z } from "zod";

import { ApiClientError, apiClient } from "@/lib/api/client";
import type {
  AssistantChatRequest,
  AssistantChatResponse,
} from "@/features/assistant/types";

const assistantSourceSchema = z.object({
  transaction_id: z.string().min(1),
  merchant: z.string().min(1),
  date: z.string().min(1),
  amount: z.number(),
});

const assistantChatSchema = z.object({
  answer: z.string().min(1),
  sources: z.array(assistantSourceSchema).default([]),
  confidence: z.number().min(0).max(1),
});

const apiEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: assistantChatSchema,
});

function toAssistantError(error: unknown): Error {
  if (error instanceof z.ZodError) {
    return new Error("Unexpected assistant response format from backend.");
  }

  if (error instanceof ApiClientError) {
    return error;
  }

  if (error instanceof Error) {
    return error;
  }

  return new Error("Unable to reach assistant service right now.");
}

export async function sendAssistantMessage(
  payload: AssistantChatRequest,
): Promise<AssistantChatResponse> {
  try {
    const response = await apiClient.post("/assistant/chat", payload);
    return apiEnvelopeSchema.parse(response.data).data;
  } catch (error) {
    throw toAssistantError(error);
  }
}
