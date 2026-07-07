import { describe, expect, it } from "vitest";

import {
  isSupportedGeminiCredential,
  normalizeGeminiCredentialInput,
} from "@/features/ai-key/credential-validation";

describe("credential-validation", () => {
  it("accepts AIza credentials", () => {
    expect(isSupportedGeminiCredential("AIza-valid-key")).toBe(true);
  });

  it("accepts AQ credentials", () => {
    expect(isSupportedGeminiCredential("AQ-valid-auth-key")).toBe(true);
  });

  it("rejects malformed credentials", () => {
    expect(isSupportedGeminiCredential("invalid-key")).toBe(false);
  });

  it("normalizes quoted input", () => {
    expect(normalizeGeminiCredentialInput('  "AQ-key" ')).toBe("AQ-key");
    expect(normalizeGeminiCredentialInput("  'AIza-key' ")).toBe("AIza-key");
  });
});
