import { CircleUserRound, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { clearStoredUser, getStoredUser } from "@/lib/auth/storage";

export function TopHeader() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const displayName = user?.name ?? "User";

  const handleLogout = () => {
    clearStoredUser();
    navigate("/", { replace: true });
  };

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6">
        <div>
          <h1 className="text-base font-semibold tracking-tight md:text-lg">
            WalletMind
          </h1>
          <p className="text-xs text-[var(--text-muted)]">
            AI Financial Concierge
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--text-muted)]">
            <CircleUserRound className="h-[var(--icon-md)] w-[var(--icon-md)]" />
            <span>Welcome back, {displayName}</span>
          </div>
          <Button variant="secondary" size="sm" onClick={handleLogout}>
            <LogOut className="mr-2 h-[var(--icon-md)] w-[var(--icon-md)]" />
            Logout
          </Button>
          <div
            aria-hidden="true"
            className="grid h-9 w-9 place-items-center rounded-full bg-[var(--primary-soft)] text-xs font-semibold text-[var(--text)]"
          >
            {displayName.charAt(0).toUpperCase()}
          </div>
        </div>
      </div>
    </header>
  );
}
