import { Bell, CircleUserRound } from "lucide-react";

import { getStoredUser } from "@/lib/auth/storage";

export function TopHeader() {
  const user = getStoredUser();
  const displayName = user?.name ?? "User";

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-3 px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-[var(--primary)] text-sm font-bold text-[var(--bg)] shadow-[var(--shadow-sm)]">
            WM
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight md:text-lg">
              WalletMind
            </h1>
            <p className="text-xs text-[var(--text-muted)]">
              AI Financial Concierge
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Notifications"
            className="grid h-9 w-9 place-items-center rounded-full border border-[var(--border)] bg-[var(--surface-soft)] text-[var(--text-muted)] transition hover:bg-[var(--surface)]"
          >
            <Bell className="h-[var(--icon-md)] w-[var(--icon-md)]" />
          </button>
          <div
            aria-hidden="true"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--text)]"
          >
            <CircleUserRound className="h-[var(--icon-md)] w-[var(--icon-md)]" />
            <span>{displayName.charAt(0).toUpperCase()}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
