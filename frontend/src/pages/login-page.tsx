import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageTitle } from "@/components/ui/section-title";
import { clearStoredUser, getStoredUser } from "@/lib/auth/storage";

export function LoginPage() {
  const navigate = useNavigate();
  const user = getStoredUser();

  useEffect(() => {
    if (user) {
      navigate("/app/home", { replace: true });
    }
  }, [navigate, user]);

  const handleContinue = () => {
    navigate("/app/home");
  };

  const handleSwitchProfile = () => {
    clearStoredUser();
    navigate("/register", { replace: true });
  };

  const handleLogout = () => {
    clearStoredUser();
    navigate("/", { replace: true });
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        <PageTitle
          title="Welcome Back"
          subtitle="Continue your WalletMind journey."
        />

        {user ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Continue as {user.name}</CardTitle>
              <CardDescription>
                WalletMind found an existing local profile.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                  <p className="text-xs text-[var(--text-muted)]">Occupation</p>
                  <p className="text-sm font-medium">{user.occupation}</p>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                  <p className="text-xs text-[var(--text-muted)]">
                    Monthly Income
                  </p>
                  <p className="text-sm font-medium">{user.monthly_income}</p>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                  <p className="text-xs text-[var(--text-muted)]">
                    Primary Goal
                  </p>
                  <p className="text-sm font-medium">
                    {user.primary_financial_goal ?? "Not set"}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={handleContinue}>Continue</Button>
                <Button variant="secondary" onClick={handleSwitchProfile}>
                  Switch Profile
                </Button>
                <Button variant="secondary" onClick={handleLogout}>
                  Logout
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                No WalletMind profile found.
              </CardTitle>
              <CardDescription>
                Create your WalletMind profile to continue.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <Link to="/register">Create Profile</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </PageWrapper>
  );
}
