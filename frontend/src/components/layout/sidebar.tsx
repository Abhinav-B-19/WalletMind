import {
  Bot,
  CircleDollarSign,
  FileStack,
  HeartPulse,
  Home,
  LogOut,
  PiggyBank,
  Settings,
  Sparkles,
  Timer,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { clearStoredUser } from "@/lib/auth/storage";
import { cn } from "@/lib/utils";

const links = [
  { to: "/app/home", label: "Home", icon: Home, comingSoon: false },
  {
    to: "/app/statements",
    label: "Statements",
    icon: FileStack,
    comingSoon: false,
  },
  {
    to: "/app/dashboard",
    label: "AI Dashboard",
    icon: CircleDollarSign,
    comingSoon: false,
  },
  {
    to: "/app/insights",
    label: "Spending Insights",
    icon: Sparkles,
    comingSoon: false,
  },
  {
    to: "/app/budget",
    label: "Budget Recommendations",
    icon: PiggyBank,
    comingSoon: false,
  },
  {
    to: "/app/health",
    label: "Financial Health",
    icon: HeartPulse,
    comingSoon: false,
  },
  {
    to: "/app/planner",
    label: "Monthly Report",
    icon: Timer,
    comingSoon: false,
  },
  { to: "/app/chat", label: "AI Assistant", icon: Bot, comingSoon: false },
  { to: "/app/settings", label: "Settings", icon: Settings, comingSoon: false },
];

export function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearStoredUser();
    navigate("/", { replace: true });
  };

  return (
    <aside className="h-full w-full border-r border-[var(--border)] bg-[var(--surface-soft)] px-3 py-4 md:w-72 md:flex-shrink-0">
      <div className="flex h-full flex-col">
        <nav aria-label="Primary" className="flex-1">
          <ul className="space-y-1">
            {links.map(({ to, label, icon: Icon, comingSoon }) => (
              <li key={label}>
                <NavLink
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm text-[var(--text-muted)] transition-colors",
                      isActive
                        ? "bg-[var(--primary-soft)] text-[var(--text)]"
                        : "hover:bg-[var(--surface)]",
                    )
                  }
                >
                  <span className="flex items-center gap-3">
                    <Icon
                      className="h-[var(--icon-md)] w-[var(--icon-md)]"
                      aria-hidden="true"
                    />
                    {label}
                  </span>
                  {comingSoon ? (
                    <Badge variant="muted">Coming Soon</Badge>
                  ) : null}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mt-6 space-y-3 border-t border-[var(--border)] px-3 pt-4">
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
