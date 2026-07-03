import { ApiClientError } from "@/lib/api/client";

export const AI_DEGRADATION_TITLE = "AI insights temporarily unavailable";
export const AI_DEGRADATION_DESCRIPTION =
  "AI insights are temporarily unavailable due to the current API usage limit. Core financial analysis remains available. Please try again later.";

const AI_DEGRADATION_CODES = new Set([
  "AI_RATE_LIMIT",
  "AI_SERVICE_ERROR",
  "AI_RESPONSE_INVALID",
  "AI_TIMEOUT",
  "AI_TIMEOUT_OR_SERVICE_ERROR",
]);

export function isAIUnavailableError(error: unknown): boolean {
  if (error instanceof ApiClientError) {
    if (error.code && AI_DEGRADATION_CODES.has(error.code)) {
      return true;
    }

    const message = error.message.toUpperCase();
    return (
      message.includes("AI_RATE_LIMIT") ||
      message.includes("AI_SERVICE_ERROR") ||
      message.includes("AI_RESPONSE_INVALID") ||
      message.includes("AI_TIMEOUT") ||
      message.includes("AI_TIMEOUT_OR_SERVICE_ERROR")
    );
  }

  if (error instanceof Error) {
    const message = error.message.toUpperCase();
    return (
      message.includes("AI_RATE_LIMIT") ||
      message.includes("AI_SERVICE_ERROR") ||
      message.includes("AI_RESPONSE_INVALID") ||
      message.includes("AI_TIMEOUT") ||
      message.includes("AI_TIMEOUT_OR_SERVICE_ERROR")
    );
  }

  return false;
}
