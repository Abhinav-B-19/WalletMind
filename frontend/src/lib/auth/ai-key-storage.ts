const AI_KEY_CONFIGURED_STORAGE_KEY = "walletmind_ai_configured";
const AI_KEY_SOURCE_STORAGE_KEY = "walletmind_ai_source";

export type AIKeySource = "session" | "developer" | "none";

export function setAIKeyStatus(configured: boolean, source: AIKeySource): void {
  localStorage.setItem(
    AI_KEY_CONFIGURED_STORAGE_KEY,
    configured ? "true" : "false",
  );
  localStorage.setItem(AI_KEY_SOURCE_STORAGE_KEY, source);
}

export function clearAIKeyStatus(): void {
  localStorage.removeItem(AI_KEY_CONFIGURED_STORAGE_KEY);
  localStorage.removeItem(AI_KEY_SOURCE_STORAGE_KEY);
}

export function isAIKeyConfigured(): boolean {
  return localStorage.getItem(AI_KEY_CONFIGURED_STORAGE_KEY) === "true";
}

export function getAIKeySource(): AIKeySource {
  const value = localStorage.getItem(AI_KEY_SOURCE_STORAGE_KEY);
  if (value === "session" || value === "developer") {
    return value;
  }
  return "none";
}

export { AI_KEY_CONFIGURED_STORAGE_KEY, AI_KEY_SOURCE_STORAGE_KEY };
