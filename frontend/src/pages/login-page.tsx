import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Search } from "lucide-react";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { LoadingState } from "@/components/ui/loading-state";
import { PageTitle } from "@/components/ui/section-title";
import { logoutUserSession } from "@/lib/api/users";
import { clearAIKeyStatus } from "@/lib/auth/ai-key-storage";
import { listUsers } from "@/lib/api/users";
import {
  clearStoredUser,
  getStoredUser,
  setStoredUser,
  type StoredWalletMindUser,
} from "@/lib/auth/storage";

type ViewState = "idle" | "loading" | "error" | "ready";

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Not available";
  }

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const activeUser = getStoredUser();
  const [profiles, setProfiles] = useState<StoredWalletMindUser[]>([]);
  const [viewState, setViewState] = useState<ViewState>("idle");
  const [searchQuery, setSearchQuery] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadProfiles = async () => {
    setViewState("loading");
    setLoadError(null);

    try {
      const users = await listUsers();
      const normalized: StoredWalletMindUser[] = users.map((user) => ({
        id: user.id,
        name: user.name,
        email: user.email ?? null,
        occupation: user.occupation,
        monthly_income: user.monthly_income,
        currency: user.currency,
        primary_financial_goal: user.primary_financial_goal ?? null,
        created_at: user.created_at ?? null,
        updated_at: user.updated_at ?? null,
      }));

      normalized.sort((left, right) =>
        left.name.localeCompare(right.name, undefined, { sensitivity: "base" }),
      );

      setProfiles(normalized);
      setViewState("ready");
    } catch (error) {
      setViewState("error");
      setLoadError(
        error instanceof Error
          ? error.message
          : "Unable to load existing profiles.",
      );
    }
  };

  useEffect(() => {
    if (!activeUser) {
      void loadProfiles();
    }
  }, [activeUser]);

  const filteredProfiles = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return profiles;
    }

    return profiles.filter((profile) => {
      const email = (profile.email ?? "").toLowerCase();
      return (
        profile.name.toLowerCase().includes(query) || email.includes(query)
      );
    });
  }, [profiles, searchQuery]);

  const redirectPath = useMemo(() => {
    const from = (location.state as { from?: string } | null)?.from;
    if (from && from.startsWith("/app")) {
      return from;
    }

    return "/app/home";
  }, [location.state]);

  const handleSelectProfile = (profile: StoredWalletMindUser) => {
    setStoredUser(profile);
    navigate(redirectPath, { replace: true });
  };

  const handleLogout = async () => {
    try {
      await logoutUserSession();
    } catch {
      // Best-effort backend session cleanup.
    }

    clearStoredUser();
    clearAIKeyStatus();
    navigate("/", { replace: true });
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        <PageTitle
          title="Existing Profiles"
          subtitle="Pick your WalletMind profile or create a new one."
        />

        {activeUser ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Continue as {activeUser.name}
              </CardTitle>
              <CardDescription>
                WalletMind found an existing local profile.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                  <p className="text-xs text-[var(--text-muted)]">Occupation</p>
                  <p className="text-sm font-medium">{activeUser.occupation}</p>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                  <p className="text-xs text-[var(--text-muted)]">
                    Monthly Income
                  </p>
                  <p className="text-sm font-medium">
                    {activeUser.monthly_income}
                  </p>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                  <p className="text-xs text-[var(--text-muted)]">
                    Primary Goal
                  </p>
                  <p className="text-sm font-medium">
                    {activeUser.primary_financial_goal ?? "Not set"}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={() => navigate(redirectPath)}>Continue</Button>
                <Button
                  variant="secondary"
                  onClick={() => navigate("/register", { replace: true })}
                >
                  Create Different Profile
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    void handleLogout();
                  }}
                >
                  Logout
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4" aria-label="Existing profiles selector">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Already have a profile?
                </CardTitle>
                <CardDescription>
                  Load an existing profile from WalletMind users and continue
                  without passwords.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-[var(--icon-sm)] w-[var(--icon-sm)] -translate-y-1/2 text-[var(--text-muted)]" />
                  <Input
                    aria-label="Search profiles"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search by name or email"
                    className="pl-9"
                  />
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button asChild>
                    <Link to="/register">Create New Profile</Link>
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => void loadProfiles()}
                  >
                    Retry
                  </Button>
                </div>
              </CardContent>
            </Card>

            {viewState === "loading" ? (
              <LoadingState title="Loading existing profiles..." />
            ) : null}
            {viewState === "error" ? (
              <ErrorState
                title="Unable to load profiles"
                description={
                  loadError ?? "Please retry to load existing profiles."
                }
              />
            ) : null}

            {viewState === "ready" && filteredProfiles.length === 0 ? (
              <EmptyState
                title="No profiles found."
                description="Try a different search term or create a new WalletMind profile."
              />
            ) : null}

            {viewState === "ready" && filteredProfiles.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {filteredProfiles.map((profile) => (
                  <Card key={profile.id}>
                    <CardContent className="space-y-4 p-5">
                      <div>
                        <h3 className="text-base font-semibold">
                          {profile.name}
                        </h3>
                        <p className="text-sm text-[var(--text-muted)]">
                          {profile.email ?? "Email not available"}
                        </p>
                      </div>

                      <dl className="grid grid-cols-2 gap-3 text-xs">
                        <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                          <dt className="text-[var(--text-muted)]">Created</dt>
                          <dd className="mt-1 text-sm font-medium">
                            {formatDate(profile.created_at)}
                          </dd>
                        </div>
                        <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
                          <dt className="text-[var(--text-muted)]">Updated</dt>
                          <dd className="mt-1 text-sm font-medium">
                            {formatDate(profile.updated_at)}
                          </dd>
                        </div>
                      </dl>

                      <Button
                        className="w-full"
                        onClick={() => handleSelectProfile(profile)}
                      >
                        Select Profile
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
