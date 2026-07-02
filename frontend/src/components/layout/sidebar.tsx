import {
  Bot,
  FileStack,
  Home,
  LayoutDashboard,
  LogOut,
  Settings,
  Timer,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { clearStoredUser } from "@/lib/auth/storage";
import { cn } from "@/lib/utils";

const links = [
  { to: "/app", label: "Home", icon: Home, end: true },
  { to: "/app/statements", label: "Statements", icon: FileStack },
  { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/planner", label: "Planner", icon: Timer },
  { to: "/app/chat", label: "AI Assistant", icon: Bot },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearStoredUser();
    navigate("/", { replace: true });
  };

  return (
    <aside className="w-full border-r border-[var(--border)] bg-[var(--surface-soft)] px-3 py-4 md:min-h-[calc(100vh-73px)] md:w-72">
      <div className="flex h-full flex-col">
        <div className="mb-6 flex items-center gap-3 px-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-[var(--primary)] text-sm font-bold text-[var(--bg)] shadow-[var(--shadow-sm)]">
            WM
          </div>
          <div>
            <p className="text-sm font-semibold">WalletMind</p>
            <p className="text-xs text-[var(--text-muted)]">
              AI Financial Concierge
            </p>
          </div>
        </div>
        <nav aria-label="Primary" className="flex-1">
          <ul className="space-y-1">
            {links.map(({ to, label, icon: Icon, end }) => (
              <li key={label}>
                <NavLink
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-[var(--text-muted)] transition-colors",
                      isActive
                        ? "bg-[var(--primary-soft)] text-[var(--text)]"
                        : "hover:bg-[var(--surface)]",
                    )
                  }
                >
                  <Icon
                    className="h-[var(--icon-md)] w-[var(--icon-md)]"
                    aria-hidden="true"
                  />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="mt-6 border-t border-[var(--border)] px-3 pt-4">
          <Button
            variant="secondary"
            className="w-full justify-start gap-3"
            onClick={handleLogout}
          >
            <LogOut className="h-[var(--icon-md)] w-[var(--icon-md)]" />
            Logout
          </Button>
        </div>
      </div>
    </aside>
  );
}
