const USER_STORAGE_KEY = "walletmind_user";

export type StoredWalletMindUser = {
  id: string;
  name: string;
  occupation: string;
  monthly_income: number;
};

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
}

export function clearStoredUser(): void {
  localStorage.removeItem(USER_STORAGE_KEY);
}

export function hasStoredUser(): boolean {
  return getStoredUser() !== null;
}

export { USER_STORAGE_KEY };
