import { describe, expect, it } from "vitest";

import {
  AI_DEGRADATION_DESCRIPTION,
  AI_DEGRADATION_TITLE,
  isAIUnavailableError,
} from "@/features/ai-dashboard/services/ai-degradation";
import { ApiClientError } from "@/lib/api/client";

describe("isAIUnavailableError", () => {
  it.each([
    "AI_RATE_LIMIT",
    "AI_SERVICE_ERROR",
    "AI_RESPONSE_INVALID",
    "AI_TIMEOUT",
  ])("returns true for %s", (code) => {
    const error = new ApiClientError("AI error", { code });
    expect(isAIUnavailableError(error)).toBe(true);
  });

  it("returns false for non-AI codes", () => {
    const error = new ApiClientError("Validation error", {
      code: "VALIDATION_ERROR",
    });

    expect(isAIUnavailableError(error)).toBe(false);
  });

  it("exports expected title and description copy", () => {
    expect(AI_DEGRADATION_TITLE).toBe("AI insights temporarily unavailable");
    expect(AI_DEGRADATION_DESCRIPTION).toContain(
      "Core financial analysis remains available",
    );
  });
});
