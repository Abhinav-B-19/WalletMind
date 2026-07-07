import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  BadgeCheck,
  Bot,
  CheckCircle2,
  Database,
  Info,
  Lock,
  X,
  Server,
  Settings2,
  Shield,
  Sparkles,
  UserCircle2,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import {
  FeatureBadge,
  InfoRow,
  ReadOnlyField,
  SettingsCard,
  SettingsSection,
  StatusBadge,
  VersionCard,
} from "@/components/settings/settings-primitives";
import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";
import {
  GeminiApiKeyManager,
  type GeminiApiKeyNotification,
} from "@/features/ai-key/gemini-api-key-manager";
import {
  useAIHealth,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";
import { getStoredUser } from "@/lib/auth/storage";
import { listStatements } from "@/lib/api/statements";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatDateTime(value: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(value);
}

function formatBytes(totalBytes: number): string {
  if (totalBytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(totalBytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = totalBytes / 1024 ** index;
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function toTitleCase(value: string): string {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function AppSettingsPage() {
  const location = useLocation();
  const aiSectionRef = useRef<HTMLElement | null>(null);
  const [aiBanner, setAIBanner] = useState<GeminiApiKeyNotification | null>(
    null,
  );

  useEffect(() => {
    if (!aiBanner?.autoDismissMs) {
      return;
    }

    const timer = window.setTimeout(() => {
      setAIBanner(null);
    }, aiBanner.autoDismissMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [aiBanner]);

  useEffect(() => {
    const query = new URLSearchParams(location.search);
    if (query.get("section") !== "ai") {
      return;
    }

    const target = aiSectionRef.current;
    if (!target) {
      return;
    }

    target.scrollIntoView?.({ behavior: "smooth", block: "start" });
    target.focus({ preventScroll: true });
  }, [location.search]);

  const user = getStoredUser();

  const statementsQuery = useQuery({
    queryKey: ["settings", "statements", user?.id],
    queryFn: () => listStatements(user?.id),
    enabled: Boolean(user?.id),
    staleTime: 1000 * 30,
    gcTime: 1000 * 60 * 5,
    retry: 1,
  });

  const processedStatementsQuery = useProcessedStatements(user?.id);
  const aiHealthQuery = useAIHealth();

  const allStatements = statementsQuery.data ?? [];
  const processedStatements = processedStatementsQuery.data ?? [];

  const profileSummary = useMemo(() => {
    const totalStatements = allStatements.length;
    const processedCount = processedStatements.length;
    const totalTransactions = allStatements.reduce(
      (total, statement) => total + statement.parsed_transaction_count,
      0,
    );
    const firstUpload =
      allStatements.length > 0
        ? [...allStatements]
            .sort(
              (left, right) =>
                new Date(left.uploaded_at).getTime() -
                new Date(right.uploaded_at).getTime(),
            )
            .at(0)
        : null;
    const storageBytes = allStatements.reduce(
      (total, statement) => total + statement.file_size,
      0,
    );

    return {
      totalStatements,
      processedCount,
      totalTransactions,
      registrationDate: firstUpload
        ? formatDate(firstUpload.uploaded_at)
        : "Future Enhancement",
      storageBytes,
    };
  }, [allStatements, processedStatements.length]);

  const aiStatus = aiHealthQuery.data?.status ?? "unavailable";
  const aiHealthy = aiStatus.toLowerCase().includes("healthy");
  const backendConnected =
    statementsQuery.isSuccess ||
    processedStatementsQuery.isSuccess ||
    aiHealthQuery.isSuccess;
  const frontendVersion = import.meta.env.VITE_APP_VERSION ?? "0.1.0";
  const pythonVersion = import.meta.env.VITE_PYTHON_VERSION ?? "3.12+";
  const fastApiVersion = import.meta.env.VITE_FASTAPI_VERSION ?? "0.115+";
  const tailwindVersion = import.meta.env.VITE_TAILWIND_VERSION ?? "4.x";
  const reactQueryVersion = import.meta.env.VITE_REACT_QUERY_VERSION ?? "5.x";
  const buildDate =
    import.meta.env.VITE_BUILD_DATE ??
    formatDateTime(new Date(document.lastModified));
  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
  const gitCommit = import.meta.env.VITE_GIT_COMMIT ?? "Future Enhancement";
  const aiModel = aiHealthQuery.data?.model ?? "gemini-2.5-flash";

  return (
    <div className="space-y-8" aria-label="WalletMind settings page">
      <PageTitle
        title="Settings"
        subtitle="Operational profile, application diagnostics, and governance details for your WalletMind workspace."
      />

      <section
        className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
        aria-label="Settings version cards"
      >
        <VersionCard
          title="WalletMind Version"
          value={frontendVersion}
          meta="Capstone release track"
        />
        <VersionCard
          title="Environment"
          value={import.meta.env.MODE}
          meta="Vite runtime mode"
        />
        <VersionCard
          title="Backend Status"
          value={backendConnected ? "Connected" : "Degraded"}
          meta={backendConnected ? "APIs reachable" : "Retry API connectivity"}
        />
        <VersionCard
          title="AI Health"
          value={toTitleCase(aiStatus)}
          meta={aiModel}
        />
      </section>

      <SettingsSection
        title="Profile"
        description="User and ingestion activity profile generated from your current workspace context."
        icon={<UserCircle2 className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <div className="grid gap-4 xl:grid-cols-2">
          <SettingsCard
            title="Identity & Activity"
            description="Read-only account profile details."
          >
            <InfoRow
              label="Application User ID"
              value={user?.id ?? "No user detected"}
            />
            <InfoRow
              label="Registration Date"
              value={profileSummary.registrationDate}
            />
            <InfoRow label="Last Active" value={formatDateTime(new Date())} />
            <InfoRow
              label="AI Requests Performed"
              value={"AI Usage Available"}
            />
          </SettingsCard>

          <SettingsCard
            title="Usage Summary"
            description="Statement pipeline and imported data metrics."
          >
            <InfoRow
              label="Uploaded Statements"
              value={`${profileSummary.totalStatements}`}
            />
            <InfoRow
              label="Processed Statements"
              value={`${profileSummary.processedCount}`}
            />
            <InfoRow
              label="Total Transactions Imported"
              value={`${profileSummary.totalTransactions}`}
            />
            <InfoRow
              label="Profile Status"
              value={
                <StatusBadge
                  label={user ? "Active" : "Guest Context"}
                  tone={user ? "healthy" : "warning"}
                />
              }
            />
          </SettingsCard>
        </div>
      </SettingsSection>

      <SettingsSection
        title="Application"
        description="Current runtime, API, and platform diagnostics from active frontend settings."
        icon={<Settings2 className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <SettingsCard
          title="Runtime Information"
          description="Build and service-level metadata."
        >
          <InfoRow label="Current Version" value={frontendVersion} />
          <InfoRow label="Build Date" value={buildDate} />
          <InfoRow label="Environment" value={import.meta.env.MODE} />
          <InfoRow
            label="Backend Status"
            value={
              <StatusBadge
                label={backendConnected ? "Connected" : "Degraded"}
                tone={backendConnected ? "healthy" : "warning"}
              />
            }
          />
          <InfoRow label="Frontend Version" value={frontendVersion} />
          <InfoRow label="API Base URL" value={apiBaseUrl} />
          <InfoRow label="Database" value="SQLite" />
          <InfoRow label="Current AI Model" value={aiModel} />
          <InfoRow
            label="AI Health Status"
            value={
              <StatusBadge
                label={toTitleCase(aiStatus)}
                tone={aiHealthy ? "healthy" : "warning"}
              />
            }
          />
        </SettingsCard>
      </SettingsSection>

      <SettingsSection
        title="AI Configuration"
        description="Manage your session-scoped Gemini API key and review active AI runtime settings."
        icon={<Bot className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <section
          id="ai-settings-section"
          aria-label="AI Settings"
          tabIndex={-1}
          ref={aiSectionRef}
          className="space-y-3"
        >
          {aiBanner ? (
            <div
              className={
                aiBanner.variant === "success"
                  ? "rounded-[var(--radius-md)] border border-emerald-500/40 bg-emerald-500/12 p-3"
                  : aiBanner.variant === "warning"
                    ? "rounded-[var(--radius-md)] border border-amber-400/50 bg-amber-400/12 p-3"
                    : "rounded-[var(--radius-md)] border border-rose-500/45 bg-rose-500/12 p-3"
              }
              data-testid="ai-settings-banner"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-2">
                    {aiBanner.variant === "success" ? (
                      <CheckCircle2 className="h-[var(--icon-md)] w-[var(--icon-md)] text-emerald-300" />
                    ) : aiBanner.variant === "warning" ? (
                      <Info className="h-[var(--icon-md)] w-[var(--icon-md)] text-amber-200" />
                    ) : (
                      <AlertCircle className="h-[var(--icon-md)] w-[var(--icon-md)] text-rose-200" />
                    )}
                    <p className="text-sm font-semibold">{aiBanner.title}</p>
                  </div>
                  <p className="text-sm text-[var(--text-muted)]">
                    {aiBanner.description}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="h-8 w-8 p-0"
                  aria-label="Dismiss AI settings banner"
                  onClick={() => setAIBanner(null)}
                >
                  <X className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                </Button>
              </div>
            </div>
          ) : null}

          <GeminiApiKeyManager
            context="settings"
            onNotification={(notification) => setAIBanner(notification)}
          />
        </section>

        <div
          className="grid gap-3 md:grid-cols-2 xl:grid-cols-3"
          data-testid="settings-grid"
        >
          <ReadOnlyField
            label="Provider"
            value="Google Gemini"
            statusLabel="Configured"
            statusTone="healthy"
          />
          <ReadOnlyField
            label="Health"
            value={aiHealthy ? "Healthy" : "Unhealthy"}
            statusLabel={aiHealthy ? "Healthy" : "Unhealthy"}
            statusTone={aiHealthy ? "healthy" : "warning"}
          />
          <ReadOnlyField label="Current Model" value={aiModel} />
          <ReadOnlyField
            label="Temperature"
            value="Future Enhancement"
            statusLabel="Future Enhancement"
            statusTone="future"
          />
          <ReadOnlyField
            label="Max Output Tokens"
            value="Future Enhancement"
            statusLabel="Future Enhancement"
            statusTone="future"
          />
          <ReadOnlyField
            label="Grounded Responses"
            value="Enabled"
            statusLabel="Enabled"
            statusTone="healthy"
          />
          <ReadOnlyField
            label="Source Attribution"
            value="Enabled"
            statusLabel="Enabled"
            statusTone="healthy"
          />
        </div>
      </SettingsSection>

      <SettingsSection
        title="Data Management"
        description="Current statement and transaction footprint in your local WalletMind workspace."
        icon={<Database className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
          <SettingsCard
            title="Data Footprint"
            description="Derived from uploaded and processed statements."
          >
            <InfoRow
              label="Uploaded Statements"
              value={`${profileSummary.totalStatements}`}
            />
            <InfoRow
              label="Processed Statements"
              value={`${profileSummary.processedCount}`}
            />
            <InfoRow
              label="Transactions"
              value={`${profileSummary.totalTransactions}`}
            />
            <InfoRow
              label="Storage Used"
              value={formatBytes(profileSummary.storageBytes)}
            />
          </SettingsCard>

          <SettingsCard
            title="Actions"
            description="Workspace data and exploration shortcuts."
          >
            <div className="flex flex-col gap-2">
              <Button asChild variant="secondary">
                <Link to="/app/statements">View Statements</Link>
              </Button>
              <Button asChild variant="secondary">
                <Link to="/app/dashboard">Open Transaction Explorer</Link>
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled
                title="Future Enhancement: Export pipeline is not enabled in this release."
                aria-label="Export data future enhancement"
              >
                Export Data (Future Enhancement)
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled
                title="Future Enhancement: Bulk deletion workflow is not enabled in this release."
                aria-label="Delete all data future enhancement"
              >
                Delete All Data (Future Enhancement)
              </Button>
            </div>
          </SettingsCard>
        </div>
      </SettingsSection>

      <SettingsSection
        title="Privacy & Security"
        description="Operational safeguards and data handling commitments."
        icon={<Shield className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <SettingsCard title="Local Processing">
            <p className="text-sm text-[var(--text-muted)]">
              Statement processing and classification operate within your
              WalletMind-managed runtime context.
            </p>
          </SettingsCard>
          <SettingsCard title="AI Responses Grounded">
            <p className="text-sm text-[var(--text-muted)]">
              Assistant and analytics outputs are grounded in deterministic
              statement data and traceable sources.
            </p>
          </SettingsCard>
          <SettingsCard title="No Banking Credentials Stored">
            <p className="text-sm text-[var(--text-muted)]">
              WalletMind does not require or persist internet banking usernames
              or passwords.
            </p>
          </SettingsCard>
          <SettingsCard title="Data Stored Locally">
            <p className="text-sm text-[var(--text-muted)]">
              Uploaded statements, parsed rows, and derived intelligence are
              persisted in local project storage.
            </p>
          </SettingsCard>
          <SettingsCard title="API Keys Session Scoped">
            <p className="text-sm text-[var(--text-muted)]">
              User-provided Gemini API keys are validated and kept in secure
              server-side session memory. Keys are not returned to browser
              clients and are removed on logout.
            </p>
          </SettingsCard>
          <SettingsCard title="Statement Processing Security">
            <p className="text-sm text-[var(--text-muted)]">
              Ingestion and parser jobs run behind validated API routes and
              typed response boundaries.
            </p>
          </SettingsCard>
        </div>
      </SettingsSection>

      <SettingsSection
        title="Application Features"
        description="Delivered product capabilities currently active in this release."
        icon={<BadgeCheck className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <div className="flex flex-wrap gap-2">
          <FeatureBadge feature="Statement Upload" />
          <FeatureBadge feature="Parser Engine" />
          <FeatureBadge feature="Transaction Intelligence" />
          <FeatureBadge feature="Spending Insights" />
          <FeatureBadge feature="Financial Health Score" />
          <FeatureBadge feature="Budget Recommendations" />
          <FeatureBadge feature="AI Assistant" />
          <FeatureBadge feature="Monthly Reports" />
        </div>
      </SettingsSection>

      <SettingsSection
        title="System Information"
        description="Framework and runtime version inventory for troubleshooting and demos."
        icon={<Server className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <SettingsCard
          title="Runtime Matrix"
          description="Stack-level implementation versions and build metadata."
        >
          <InfoRow label="Python Version" value={pythonVersion} />
          <InfoRow label="React Version" value="19.2.7" />
          <InfoRow label="FastAPI" value={fastApiVersion} />
          <InfoRow label="SQLite" value="Enabled" />
          <InfoRow label="Tailwind" value={tailwindVersion} />
          <InfoRow label="React Query" value={reactQueryVersion} />
          <InfoRow label="Gemini" value={aiModel} />
          <InfoRow label="Last Build" value={buildDate} />
          <InfoRow label="Git Commit" value={gitCommit} />
          <InfoRow label="Environment" value={import.meta.env.MODE} />
        </SettingsCard>
      </SettingsSection>

      <SettingsSection
        title="About"
        description="Project identity, mission, and official references."
        icon={<Info className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />}
      >
        <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
          <SettingsCard
            title="WalletMind"
            description="AI-first financial intelligence platform."
          >
            <InfoRow label="Version" value={frontendVersion} />
            <InfoRow
              label="Purpose"
              value="Transform uploaded bank statements into grounded insights, health diagnostics, and monthly recommendations."
            />
            <InfoRow
              label="Built For"
              value="Google AI Agents Intensive Capstone"
            />
            <InfoRow
              label="Technology Stack"
              value="React, TypeScript, React Query, Recharts, Tailwind, FastAPI, SQLAlchemy, Gemini"
            />
          </SettingsCard>

          <SettingsCard
            title="Links"
            description="Primary references and documentation."
          >
            <div className="flex flex-col gap-2">
              <Button asChild variant="secondary">
                <a
                  href="https://github.com/Abhinav-B-19/WalletMind"
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Open WalletMind GitHub repository"
                >
                  GitHub Repository
                </a>
              </Button>
              <Button asChild variant="secondary">
                <a
                  href="https://github.com/Abhinav-B-19/WalletMind#readme"
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Open WalletMind documentation"
                >
                  Documentation
                </a>
              </Button>
              <Button asChild variant="secondary">
                <a
                  href="https://github.com/Abhinav-B-19/WalletMind/blob/main/PROJECT_CONTEXT.md"
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Open WalletMind project context"
                >
                  PROJECT_CONTEXT
                </a>
              </Button>
            </div>
          </SettingsCard>
        </div>
      </SettingsSection>

      {statementsQuery.isError ||
      processedStatementsQuery.isError ||
      aiHealthQuery.isError ? (
        <div className="rounded-[var(--radius-md)] border border-amber-400/50 bg-amber-400/15 px-4 py-3 text-sm text-amber-100">
          <div className="inline-flex items-center gap-2">
            <Lock className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            <span>
              Some operational metrics could not be refreshed. Existing cached
              data is still shown where available.
            </span>
          </div>
        </div>
      ) : null}

      <div className="inline-flex items-center gap-2 text-xs text-[var(--text-muted)]">
        <Sparkles className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
        <span>
          All settings are read-only in this release to preserve deterministic
          platform behavior.
        </span>
      </div>
    </div>
  );
}
