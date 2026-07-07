const USER_STORAGE_KEY = "walletmind_user";
const REMEMBERED_PROFILES_STORAGE_KEY = "walletmind_profiles";
const AI_KEY_CONFIGURED_STORAGE_KEY = "walletmind_ai_configured";
const AI_KEY_SOURCE_STORAGE_KEY = "walletmind_ai_source";

export type StoredWalletMindUser = {
  id: string;
  name: string;
  email?: string | null;
  occupation: string;
  monthly_income: number;
  currency: string;
  primary_financial_goal?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

function parseRememberedUsers(raw: string | null): StoredWalletMindUser[] {
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as StoredWalletMindUser[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    localStorage.removeItem(REMEMBERED_PROFILES_STORAGE_KEY);
    return [];
  }
}

function upsertRememberedUser(user: StoredWalletMindUser): void {
  const remembered = getRememberedUsers().filter((item) => item.id !== user.id);
  remembered.push(user);
  remembered.sort((left, right) =>
    left.name.localeCompare(right.name, undefined, { sensitivity: "base" }),
  );
  localStorage.setItem(
    REMEMBERED_PROFILES_STORAGE_KEY,
    JSON.stringify(remembered),
  );
}

export function getStoredUser(): StoredWalletMindUser | null {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredWalletMindUser;
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}

export function setStoredUser(user: StoredWalletMindUser): void {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  upsertRememberedUser(user);
}

export function clearStoredUser(): void {
  localStorage.removeItem(USER_STORAGE_KEY);
  localStorage.removeItem(AI_KEY_CONFIGURED_STORAGE_KEY);
  localStorage.removeItem(AI_KEY_SOURCE_STORAGE_KEY);
}

export function hasStoredUser(): boolean {
  return getStoredUser() !== null;
}

export function getRememberedUsers(): StoredWalletMindUser[] {
  return parseRememberedUsers(
    localStorage.getItem(REMEMBERED_PROFILES_STORAGE_KEY),
  );
}

export { USER_STORAGE_KEY, REMEMBERED_PROFILES_STORAGE_KEY };
