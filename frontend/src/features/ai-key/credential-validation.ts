const SUPPORTED_GEMINI_PREFIXES = ["AIza", "AQ"] as const;

export function normalizeGeminiCredentialInput(rawValue: string): string {
  const trimmed = rawValue.trim();
  if (trimmed.length < 2) {
    return trimmed;
  }

  const startsWithSingle = trimmed.startsWith("'");
  const endsWithSingle = trimmed.endsWith("'");
  const startsWithDouble = trimmed.startsWith('"');
  const endsWithDouble = trimmed.endsWith('"');

  if (
    (startsWithSingle && endsWithSingle) ||
    (startsWithDouble && endsWithDouble)
  ) {
    return trimmed.slice(1, -1).trim();
  }

  return trimmed;
}

export function isSupportedGeminiCredential(value: string): boolean {
  return SUPPORTED_GEMINI_PREFIXES.some((prefix) => value.startsWith(prefix));
}
