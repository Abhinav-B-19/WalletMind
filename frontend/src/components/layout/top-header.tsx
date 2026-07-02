import { Bell, CircleUserRound } from "lucide-react";

import { getStoredUser } from "@/lib/auth/storage";

export function TopHeader() {
  const user = getStoredUser();
  const displayName = user?.name ?? "User";
  const currentDate = new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6">
        <div>
          <h1 className="text-base font-semibold tracking-tight md:text-lg">Welcome back, {displayName}</h1>
          <p className="text-xs text-[var(--text-muted)]">{currentDate}</p>
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
