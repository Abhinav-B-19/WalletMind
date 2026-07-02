import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";
import { getStoredUser } from "@/lib/auth/storage";

export function LoginPage() {
  const navigate = useNavigate();
  const user = getStoredUser();

  useEffect(() => {
    if (user) {
      navigate("/app", { replace: true });
    }
  }, [navigate, user]);

  const handleContinue = () => {
    navigate("/app");
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        <PageTitle
          title="Continue to WalletMind"
          subtitle="Temporary login flow until backend authentication is available."
        />

        {user ? (
          <div className="space-y-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-5">
            <p className="text-sm text-[var(--text-muted)]">
              Profile found for{" "}
              <span className="font-semibold text-[var(--text)]">
                {user.name}
              </span>
              .
            </p>
            <Button onClick={handleContinue}>Continue</Button>
          </div>
        ) : (
          <div className="space-y-4">
            <EmptyState
              title="No WalletMind profile found"
              description="Create your profile to continue."
            />
            <Button asChild>
              <Link to="/register">Create Profile</Link>
            </Button>
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
