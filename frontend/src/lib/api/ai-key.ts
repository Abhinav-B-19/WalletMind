import { z } from "zod";

import { ApiClientError, apiClient } from "@/lib/api/client";

const statusSchema = z.object({
  configured: z.boolean(),
  masked_key: z.string().nullable(),
  source: z.enum(["session", "developer", "none"]),
  model: z.string(),
  last_validated: z.string().nullable(),
});

const revealSchema = z.object({
  configured: z.boolean(),
  source: z.literal("session"),
  api_key: z.string().min(1),
});

const successSchema = z.object({
  success: z.boolean(),
});

export type GeminiKeyStatus = z.infer<typeof statusSchema>;
export type GeminiKeyReveal = z.infer<typeof revealSchema>;

function toSafeError(error: unknown, fallbackMessage: string): Error {
  if (error instanceof ApiClientError) {
    return error;
  }
  if (error instanceof Error) {
    return error;
  }
  return new Error(fallbackMessage);
}

export async function getGeminiKeyStatus(): Promise<GeminiKeyStatus> {
  try {
    const response = await apiClient.get("/ai/api-key/status");
    return statusSchema.parse(response.data);
  } catch (error) {
    throw toSafeError(error, "Unable to load Gemini key status.");
  }
}

export async function getGeminiApiKeyForReveal(): Promise<GeminiKeyReveal> {
  try {
    const response = await apiClient.get("/ai/api-key");
    return revealSchema.parse(response.data);
  } catch (error) {
    throw toSafeError(error, "Unable to reveal Gemini API key.");
  }
}

export async function setGeminiApiKey(apiKey: string): Promise<void> {
  try {
    const response = await apiClient.post("/ai/api-key", { api_key: apiKey });
    successSchema.parse(response.data);
  } catch (error) {
    throw toSafeError(error, "Unable to validate Gemini API key.");
  }
}

export async function deleteGeminiApiKey(): Promise<void> {
  try {
    const response = await apiClient.delete("/ai/api-key");
    successSchema.parse(response.data);
  } catch (error) {
    throw toSafeError(error, "Unable to remove Gemini API key.");
  }
}
