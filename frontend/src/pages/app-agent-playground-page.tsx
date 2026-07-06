import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  AlertTriangle,
  Bot,
  Brain,
  CheckCircle2,
  Clock3,
  HeartPulse,
  LoaderCircle,
  PiggyBank,
  Play,
  Sparkles,
  Timer,
  XCircle,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { PageTitle } from "@/components/ui/section-title";
import {
  executeAgents,
  executionModeSchema,
  type AgentExecutionMode,
} from "@/lib/api/agents";
import { ApiClientError } from "@/lib/api/client";
import { listStatements, type UploadedStatement } from "@/lib/api/statements";
import { listUsers, type WalletMindUser } from "@/lib/api/users";
import { getStoredUser } from "@/lib/auth/storage";
import { cn } from "@/lib/utils";

const DEFAULT_SESSION_ID = "walletmind-session";
const DEFAULT_DEMO_QUERY =
  "Analyze my finances and provide a complete financial health assessment with spending insights, personalized budget recommendations, a monthly financial report, and actionable advice to improve my financial future.";

type FriendlyErrorState = {
  title: string;
  description: string;
};

type StatusKind = "COMPLETED" | "FAILED" | "STARTED" | "SKIPPED" | "UNKNOWN";

type CoordinatorDecisionRecord = {
  intent?: string;
  capabilities?: string[];
  selected_agents?: string[];
  reason?: string;
  execution_mode?: string;
  execution_timestamp?: string;
};

type CoordinatorTraceStep = {
  agent_name?: string;
  status?: string;
  execution_order?: number;
  duration_ms?: number;
  started_at?: string;
  ended_at?: string;
  error?: string | null;
};

type CoordinatorAgentResult = {
  agent_name?: string;
  status?: string;
  errors?: string[];
  result?: unknown;
};

type CoordinatorDashboardData = {
  overall_status?: string;
  decision_record?: CoordinatorDecisionRecord;
  execution_trace?: CoordinatorTraceStep[];
  individual_agent_results?: CoordinatorAgentResult[];
  metadata?: Record<string, unknown>;
};

type ExecutionToastState = {
  kind: "success" | "warning";
  title: string;
  body: string;
  status: string;
  successfulCount: number;
  failedCount: number;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toDisplayStatus(value: unknown): StatusKind {
  const status = typeof value === "string" ? value.toUpperCase() : "UNKNOWN";

  if (status === "COMPLETED") {
    return "COMPLETED";
  }

  if (status === "FAILED") {
    return "FAILED";
  }

  if (status === "STARTED") {
    return "STARTED";
  }

  if (status === "SKIPPED") {
    return "SKIPPED";
  }

  return "UNKNOWN";
}

function formatStatusLabel(status: StatusKind): string {
  if (status === "UNKNOWN") {
    return "Unknown";
  }

  return `${status.charAt(0)}${status.slice(1).toLowerCase()}`;
}

function formatStatementOption(statement: UploadedStatement): string {
  const uploadedDate = new Date(statement.uploaded_at).toLocaleDateString();
  const status = statement.analysis_status.replace(/_/g, " ");
  return `${statement.original_filename} • ${uploadedDate} • ${status}`;
}

function isProcessedStatement(statement: UploadedStatement): boolean {
  const status = (statement.status ?? "").toLowerCase();
  const analysisStatus = (statement.analysis_status ?? "").toLowerCase();

  const processedStatuses = new Set([
    "processed",
    "ready_for_analysis",
    "analysis_pending",
    "parsed",
    "completed",
  ]);

  const blockedStatuses = new Set([
    "queued",
    "uploaded",
    "classifying",
    "classified",
    "processing",
    "ready_for_parsing",
    "parse_failed",
    "failed",
  ]);

  if (blockedStatuses.has(status) || blockedStatuses.has(analysisStatus)) {
    return false;
  }

  return processedStatuses.has(status) || processedStatuses.has(analysisStatus);
}

function formatDateTime(value: string | undefined): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatDurationMs(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }

  if (value < 1000) {
    return `${Math.round(value)} ms`;
  }

  return `${(value / 1000).toFixed(2)} s`;
}

function formatUnknown(value: unknown, fallback: string): string {
  if (value === null || value === undefined) {
    return fallback;
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return `${value}`;
  }

  return fallback;
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }

  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function buildExecutionToast(
  coordinatorData: CoordinatorDashboardData,
): ExecutionToastState {
  const status = formatStatusLabel(toDisplayStatus(coordinatorData.overall_status));

  const metadataSuccessful = toNumber(coordinatorData.metadata?.successful_agent_count);
  const metadataFailed = toNumber(coordinatorData.metadata?.failed_agent_count);

  const successfulCount =
    metadataSuccessful ??
    (coordinatorData.individual_agent_results ?? []).filter(
      (agent) => toDisplayStatus(agent.status) === "COMPLETED",
    ).length;

  const failedCount =
    metadataFailed ??
    (coordinatorData.individual_agent_results ?? []).filter(
      (agent) => toDisplayStatus(agent.status) === "FAILED",
    ).length;

  if (failedCount > 0) {
    return {
      kind: "warning",
      title: "Analysis Completed with Warnings",
      body: `${successfulCount} of ${successfulCount + failedCount} agents completed successfully.`,
      status,
      successfulCount,
      failedCount,
    };
  }

  return {
    kind: "success",
    title: "Analysis Complete",
    body: "WalletMind successfully executed the selected AI agents.",
    status,
    successfulCount,
    failedCount,
  };
}

function toFriendlyError(error: unknown): FriendlyErrorState {
  if (error instanceof ApiClientError) {
    return {
      title: "Unable to execute agents right now.",
      description:
        error.message || "Please verify your selection and try again.",
    };
  }

  if (error instanceof Error) {
    return {
      title: "Unable to execute agents right now.",
      description: error.message,
    };
  }

  return {
    title: "Unable to execute agents right now.",
    description: "Please verify your selection and try again.",
  };
}

function toCoordinatorData(payload: unknown): CoordinatorDashboardData | null {
  if (!isRecord(payload)) {
    return null;
  }

  const data = payload.data;
  if (!isRecord(data)) {
    return null;
  }

  return {
    overall_status:
      typeof data.overall_status === "string" ? data.overall_status : undefined,
    decision_record: isRecord(data.decision_record)
      ? (data.decision_record as CoordinatorDecisionRecord)
      : undefined,
    execution_trace: Array.isArray(data.execution_trace)
      ? (data.execution_trace as CoordinatorTraceStep[])
      : [],
    individual_agent_results: Array.isArray(data.individual_agent_results)
      ? (data.individual_agent_results as CoordinatorAgentResult[])
      : [],
    metadata: isRecord(data.metadata)
      ? (data.metadata as Record<string, unknown>)
      : {},
  };
}

function StatusBadge({ status }: { status: StatusKind }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold",
        status === "COMPLETED" && "bg-emerald-100 text-emerald-700",
        status === "FAILED" && "bg-rose-100 text-rose-700",
        status === "STARTED" && "bg-sky-100 text-sky-700",
        status === "SKIPPED" && "bg-amber-100 text-amber-700",
        status === "UNKNOWN" && "bg-slate-100 text-slate-700",
      )}
      aria-label={`Status: ${formatStatusLabel(status)}`}
    >
      {formatStatusLabel(status)}
    </span>
  );
}

function AgentIcon({ agentName }: { agentName: string | undefined }) {
  const normalized = agentName ?? "";

  const Icon =
    normalized === "health_agent"
      ? HeartPulse
      : normalized === "insights_agent"
        ? Sparkles
        : normalized === "budget_agent"
          ? PiggyBank
          : normalized === "report_agent"
            ? Timer
            : normalized === "assistant_agent"
              ? Bot
              : Brain;

  return <Icon className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--text-muted)]" aria-hidden="true" />;
}

function findAgentResult(
  results: CoordinatorAgentResult[],
  agentName: string,
): CoordinatorAgentResult | null {
  return (
    results.find((candidate) => candidate.agent_name === agentName) ?? null
  );
}

function extractAgentServiceData(agentResult: CoordinatorAgentResult | null): Record<string, unknown> | null {
  if (!agentResult || !isRecord(agentResult.result)) {
    return null;
  }

  const executionResult = agentResult.result.result;
  if (!isRecord(executionResult)) {
    return null;
  }

  const toolResultData = executionResult.data;
  if (!isRecord(toolResultData)) {
    return null;
  }

  return toolResultData;
}

function agentErrorText(agentResult: CoordinatorAgentResult | null): string {
  if (!agentResult || !Array.isArray(agentResult.errors) || agentResult.errors.length === 0) {
    return "Agent did not return additional failure details.";
  }

  return agentResult.errors.join("; ");
}

function ResultCardShell({
  title,
  agentName,
  status,
  children,
}: {
  title: string;
  agentName: string;
  status: StatusKind;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AgentIcon agentName={agentName} />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <StatusBadge status={status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">{children}</CardContent>
    </Card>
  );
}

function LoadingExperienceCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <LoaderCircle className="h-[var(--icon-md)] w-[var(--icon-md)] animate-spin" />
          Running Multi-Agent Execution
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-[var(--text-muted)]">
          WalletMind is orchestrating agents and collecting results from each specialist.
        </p>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="h-20 animate-pulse rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)]" />
          <div className="h-20 animate-pulse rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)]" />
          <div className="h-20 animate-pulse rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)]" />
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyExecutionState({
  hasProcessedStatements,
  onGoToUpload,
}: {
  hasProcessedStatements: boolean;
  onGoToUpload: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Execution Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        {hasProcessedStatements ? (
          <p className="text-sm text-[var(--text-muted)]">
            Run an agent execution to view coordinator summary, timeline, per-agent output cards, and workflow diagnostics.
          </p>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-[var(--text-muted)]">
              No processed statements available.
            </p>
            <p className="text-sm text-[var(--text-muted)]">
              Upload and process a statement first, then return here.
            </p>
            <Button variant="secondary" onClick={onGoToUpload}>
              Go to Statement Upload
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ExecutionToast({
  toast,
  onDismiss,
  onViewResults,
}: {
  toast: ExecutionToastState;
  onDismiss: () => void;
  onViewResults: () => void;
}) {
  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 w-[min(92vw,420px)] rounded-[var(--radius-lg)] border p-4 shadow-[var(--shadow-md)]",
        toast.kind === "success"
          ? "border-emerald-500/40 bg-emerald-950/70"
          : "border-amber-500/40 bg-amber-950/70",
      )}
      role="status"
      aria-live="polite"
      aria-label="Execution completion notification"
      data-testid="execution-toast"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-sm font-semibold">{toast.title}</p>
          <p className="text-sm text-[var(--text-muted)]">{toast.body}</p>
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={onDismiss}
          aria-label="Dismiss execution notification"
        >
          <X className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
        </Button>
      </div>
      <div className="mt-3 space-y-1 text-xs text-[var(--text-muted)]">
        <p>
          Overall status: <span className="font-semibold text-[var(--text)]">{toast.status}</span>
        </p>
        <p>
          Successful agents: <span className="font-semibold text-[var(--text)]">{toast.successfulCount}</span>
        </p>
        <p>
          Failed agents: <span className="font-semibold text-[var(--text)]">{toast.failedCount}</span>
        </p>
      </div>
      <div className="mt-3">
        <Button type="button" size="sm" onClick={onViewResults}>
          View Results
        </Button>
      </div>
    </div>
  );
}

export function AppAgentPlaygroundPage() {
  const navigate = useNavigate();
  const storedUser = getStoredUser();
  const [query, setQuery] = useState(DEFAULT_DEMO_QUERY);
  const [executionMode, setExecutionMode] = useState<AgentExecutionMode>(
    executionModeSchema.enum.multi,
  );
  const [sessionId, setSessionId] = useState(DEFAULT_SESSION_ID);
  const [showDemoBanner, setShowDemoBanner] = useState(true);
  const [executionToast, setExecutionToast] =
    useState<ExecutionToastState | null>(null);
  const [resultsHighlighted, setResultsHighlighted] = useState(false);

  const resultsRef = useRef<HTMLElement | null>(null);
  const highlightTimeoutRef = useRef<number | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const [users, setUsers] = useState<WalletMindUser[]>([]);
  const [selectedUserUuid, setSelectedUserUuid] = useState(
    storedUser?.id ?? "",
  );
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);

  const [statements, setStatements] = useState<UploadedStatement[]>([]);
  const [selectedStatementUuid, setSelectedStatementUuid] = useState("");
  const [statementsLoading, setStatementsLoading] = useState(false);
  const [statementsError, setStatementsError] = useState<string | null>(null);

  const [isExecuting, setIsExecuting] = useState(false);
  const [responsePayload, setResponsePayload] = useState<unknown | null>(null);
  const [executionError, setExecutionError] =
    useState<FriendlyErrorState | null>(null);
  const reducedMotion = prefersReducedMotion();

  useEffect(() => {
    return () => {
      if (highlightTimeoutRef.current !== null) {
        window.clearTimeout(highlightTimeoutRef.current);
      }

      if (toastTimeoutRef.current !== null) {
        window.clearTimeout(toastTimeoutRef.current);
      }
    };
  }, []);

  const userLabel = useMemo(() => {
    if (!storedUser) {
      return null;
    }

    return `${storedUser.name} (${storedUser.id})`;
  }, [storedUser]);

  useEffect(() => {
    let active = true;

    if (storedUser?.id) {
      setSelectedUserUuid(storedUser.id);
      setUsersError(null);
      return () => {
        active = false;
      };
    }

    async function loadUsers() {
      setUsersLoading(true);
      setUsersError(null);

      try {
        const response = await listUsers();
        if (!active) {
          return;
        }

        setUsers(response);
        if (response.length > 0) {
          setSelectedUserUuid((previous) => previous || response[0].id);
        }
      } catch {
        if (!active) {
          return;
        }

        setUsersError(
          "Unable to load users right now. Please refresh and retry.",
        );
      } finally {
        if (active) {
          setUsersLoading(false);
        }
      }
    }

    void loadUsers();

    return () => {
      active = false;
    };
  }, [storedUser]);

  useEffect(() => {
    let active = true;

    async function loadStatementsForUser() {
      if (!selectedUserUuid) {
        setStatements([]);
        setSelectedStatementUuid("");
        return;
      }

      setStatementsLoading(true);
      setStatementsError(null);

      try {
        const response = await listStatements(selectedUserUuid);
        if (!active) {
          return;
        }

        const processedCandidates = response.filter(isProcessedStatement);
        setStatements(response);
        setSelectedStatementUuid((previous) => {
          if (
            previous &&
            response.some((statement) => statement.statement_uuid === previous)
          ) {
            return previous;
          }
          return processedCandidates[0]?.statement_uuid ?? "";
        });
      } catch {
        if (!active) {
          return;
        }

        setStatements([]);
        setSelectedStatementUuid("");
        setStatementsError(
          "Unable to load statements for this user. Please try a different user or retry.",
        );
      } finally {
        if (active) {
          setStatementsLoading(false);
        }
      }
    }

    void loadStatementsForUser();

    return () => {
      active = false;
    };
  }, [selectedUserUuid]);

  const canExecute =
    query.trim().length > 0 &&
    selectedUserUuid.length > 0 &&
    selectedStatementUuid.length > 0 &&
    !isExecuting;

  const hasProcessedStatements = useMemo(
    () => statements.some(isProcessedStatement),
    [statements],
  );

  const clearToastTimer = () => {
    if (toastTimeoutRef.current !== null) {
      window.clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  };

  const dismissExecutionToast = () => {
    clearToastTimer();
    setExecutionToast(null);
  };

  const executeRequest = async () => {
    if (isExecuting) {
      return;
    }

    if (!query.trim() || !selectedUserUuid || !selectedStatementUuid) {
      setExecutionError({
        title: "Missing required information.",
        description:
          "Provide a query, select a user, and choose a statement before executing agents.",
      });
      return;
    }

    setIsExecuting(true);
    setExecutionError(null);
    dismissExecutionToast();
    setResponsePayload(null);

    try {
      const response = await executeAgents({
        query: query.trim(),
        user_id: storedUser?.id ?? "playground-user",
        session_id: sessionId.trim() || DEFAULT_SESSION_ID,
        user_uuid: selectedUserUuid,
        inputs: {
          statement_uuid: selectedStatementUuid,
          execution_mode:
            executionMode === executionModeSchema.enum.single
              ? "single_agent"
              : "multi_agent",
        },
      });

      setResponsePayload(response);
    } catch (error) {
      setExecutionError(toFriendlyError(error));
    } finally {
      setIsExecuting(false);
    }
  };

  const coordinatorData = useMemo(
    () => toCoordinatorData(responsePayload),
    [responsePayload],
  );

  const timeline = useMemo(
    () =>
      [...(coordinatorData?.execution_trace ?? [])].sort(
        (left, right) =>
          (left.execution_order ?? Number.MAX_SAFE_INTEGER) -
          (right.execution_order ?? Number.MAX_SAFE_INTEGER),
      ),
    [coordinatorData],
  );

  const agentResults = coordinatorData?.individual_agent_results ?? [];

  const healthAgent = findAgentResult(agentResults, "health_agent");
  const insightsAgent = findAgentResult(agentResults, "insights_agent");
  const budgetAgent = findAgentResult(agentResults, "budget_agent");
  const reportAgent = findAgentResult(agentResults, "report_agent");
  const assistantAgent = findAgentResult(agentResults, "assistant_agent");

  const healthData = extractAgentServiceData(healthAgent);
  const insightsData = extractAgentServiceData(insightsAgent);
  const budgetData = extractAgentServiceData(budgetAgent);
  const reportData = extractAgentServiceData(reportAgent);
  const assistantData = extractAgentServiceData(assistantAgent);

  const failedAgents = useMemo(
    () =>
      agentResults.filter(
        (agent) => toDisplayStatus(agent.status) === "FAILED",
      ),
    [agentResults],
  );

  const scrollToResults = () => {
    const resultsNode = resultsRef.current;
    if (!resultsNode) {
      return;
    }

    resultsNode.scrollIntoView({
      behavior: prefersReducedMotion() ? "auto" : "smooth",
      block: "start",
    });

    resultsNode.focus({ preventScroll: true });
    setResultsHighlighted(true);

    if (highlightTimeoutRef.current !== null) {
      window.clearTimeout(highlightTimeoutRef.current);
    }

    highlightTimeoutRef.current = window.setTimeout(() => {
      setResultsHighlighted(false);
      highlightTimeoutRef.current = null;
    }, 2500);
  };

  useEffect(() => {
    if (isExecuting || !coordinatorData || executionError) {
      return;
    }

    setExecutionToast(buildExecutionToast(coordinatorData));

    let secondFrame: number | null = null;
    const firstFrame = window.requestAnimationFrame(() => {
      secondFrame = window.requestAnimationFrame(() => {
        scrollToResults();
      });
    });

    return () => {
      window.cancelAnimationFrame(firstFrame);
      if (secondFrame !== null) {
        window.cancelAnimationFrame(secondFrame);
      }
    };
  }, [coordinatorData, executionError, isExecuting]);

  useEffect(() => {
    clearToastTimer();

    if (!executionToast) {
      return;
    }

    toastTimeoutRef.current = window.setTimeout(() => {
      setExecutionToast(null);
      toastTimeoutRef.current = null;
    }, 5000);

    return () => {
      clearToastTimer();
    };
  }, [executionToast]);

  return (
    <div className="space-y-6">
      <PageTitle
        title="Agent Playground"
        subtitle="Interact directly with WalletMind's ADK-powered multi-agent system."
      />

      {showDemoBanner ? (
        <Card className="border-[var(--ring)]/40 bg-[var(--primary-soft)]/30">
          <CardContent className="flex items-start justify-between gap-3 p-4">
            <div className="space-y-1">
              <p className="text-sm font-semibold">Demo Mode</p>
              <p className="text-sm text-[var(--text-muted)]">
                WalletMind is pre-configured to demonstrate complete multi-agent financial analysis.
              </p>
              <p className="text-sm text-[var(--text-muted)]">
                Simply click Execute Agents to see the Coordinator orchestrate Health, Insights, Budget, Report, and Assistant agents.
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowDemoBanner(false)}
              aria-label="Dismiss demo banner"
            >
              <X className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Execution Form</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <label className="block space-y-2">
            <span className="text-sm font-medium">Natural language query</span>
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              rows={5}
              placeholder="Analyze my finances and highlight spending risks for this statement."
              className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text)] shadow-[var(--shadow-inset)] outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
            />
          </label>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Execution Mode</legend>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="execution-mode"
                  checked={executionMode === executionModeSchema.enum.single}
                  onChange={() =>
                    setExecutionMode(executionModeSchema.enum.single)
                  }
                />
                Single Agent
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="execution-mode"
                  checked={executionMode === executionModeSchema.enum.multi}
                  onChange={() =>
                    setExecutionMode(executionModeSchema.enum.multi)
                  }
                />
                Multi Agent
              </label>
            </div>
          </fieldset>

          <label className="block space-y-2">
            <span className="text-sm font-medium">User selector</span>
            {storedUser?.id ? (
              <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-sm">
                {userLabel}
              </div>
            ) : (
              <>
                <Select
                  value={selectedUserUuid}
                  onChange={(event) => setSelectedUserUuid(event.target.value)}
                  disabled={usersLoading || users.length === 0}
                >
                  <option value="">Select a user</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name} ({user.id})
                    </option>
                  ))}
                </Select>
                {usersError ? (
                  <p className="text-sm text-[var(--danger)]">{usersError}</p>
                ) : null}
              </>
            )}
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium">Session ID</span>
            <input
              value={sessionId}
              onChange={(event) => setSessionId(event.target.value)}
              className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text)] shadow-[var(--shadow-inset)] outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
            />
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium">Statement selector</span>
            <Select
              value={selectedStatementUuid}
              onChange={(event) => setSelectedStatementUuid(event.target.value)}
              disabled={statementsLoading || statements.length === 0}
            >
              <option value="">Select a statement</option>
              {statements.map((statement) => (
                <option
                  key={statement.statement_uuid}
                  value={statement.statement_uuid}
                >
                  {formatStatementOption(statement)}
                </option>
              ))}
            </Select>
            {statementsError ? (
              <p className="text-sm text-[var(--danger)]">{statementsError}</p>
            ) : null}
            {!statementsLoading && !hasProcessedStatements ? (
              <p className="text-sm text-[var(--text-muted)]">
                Upload and process a bank statement to use the Agent Playground.
              </p>
            ) : null}
          </label>

          {executionError ? (
            <div className="rounded-[var(--radius-md)] border border-[var(--danger)]/40 bg-[var(--danger)]/10 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex gap-2">
                  <AlertTriangle className="mt-0.5 h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--danger)]" />
                  <div>
                    <p className="text-sm font-semibold text-[var(--danger)]">
                      {executionError.title}
                    </p>
                    <p className="text-sm text-[var(--text-muted)]">
                      {executionError.description}
                    </p>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => void executeRequest()}
                  disabled={isExecuting}
                >
                  Retry
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setExecutionError(null)}
                  aria-label="Dismiss error notification"
                >
                  <X className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                </Button>
              </div>
            </div>
          ) : null}

          <div>
            <Button
              onClick={() => void executeRequest()}
              disabled={!canExecute}
              className="gap-2"
            >
              {isExecuting ? (
                <>
                  <LoaderCircle className="h-[var(--icon-md)] w-[var(--icon-md)] animate-spin" />
                  WalletMind is coordinating AI agents...
                </>
              ) : (
                <>
                  <Play className="h-[var(--icon-md)] w-[var(--icon-md)]" />
                  Execute Agents
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {isExecuting && !coordinatorData ? <LoadingExperienceCard /> : null}
      {!isExecuting && !coordinatorData ? (
        <EmptyExecutionState
          hasProcessedStatements={hasProcessedStatements}
          onGoToUpload={() => navigate("/app/statements/upload")}
        />
      ) : null}

      {coordinatorData ? (
        <section
          ref={resultsRef}
          tabIndex={-1}
          aria-label="Execution results section"
          className={cn(
            "space-y-4 rounded-[var(--radius-lg)] transition-[box-shadow,border-color,background-color] duration-300 focus-visible:outline-none",
            resultsHighlighted
              ? cn(
                  "results-highlight border border-[var(--ring)]/70 bg-[var(--ring)]/5 px-2 py-2",
                  reducedMotion
                    ? "results-highlight-reduced-motion"
                    : "results-highlight-animated",
                )
              : "",
          )}
          data-testid="results-section"
        >
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Results</h2>
            <p className="text-sm text-[var(--text-muted)]">
              Review coordinator summary, timeline, and each agent's output.
            </p>
          </div>
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="text-lg">Coordinator Summary</CardTitle>
                <StatusBadge
                  status={toDisplayStatus(coordinatorData.overall_status)}
                />
              </div>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-[var(--text-muted)]">Intent</p>
                <p className="font-semibold">
                  {coordinatorData.decision_record?.intent ?? "-"}
                </p>
              </div>
              <div>
                <p className="text-[var(--text-muted)]">Execution Mode</p>
                <p className="font-semibold">
                  {coordinatorData.decision_record?.execution_mode ?? "-"}
                </p>
              </div>
              <div>
                <p className="text-[var(--text-muted)]">Selected Agents</p>
                <p className="font-semibold">
                  {formatUnknown(coordinatorData.metadata?.selected_agent_count, "0")}
                </p>
              </div>
              <div>
                <p className="text-[var(--text-muted)]">Timestamp</p>
                <p className="font-semibold">
                  {formatDateTime(
                    coordinatorData.decision_record?.execution_timestamp,
                  )}
                </p>
              </div>
              <div className="md:col-span-2 lg:col-span-4">
                <p className="text-[var(--text-muted)]">Decision Reason</p>
                <p>
                  {coordinatorData.decision_record?.reason ??
                    "No decision narrative was returned."}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Execution Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              {timeline.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  Timeline was not provided by the coordinator.
                </p>
              ) : (
                <ol className="space-y-3">
                  {timeline.map((step, index) => {
                    const status = toDisplayStatus(step.status);
                    return (
                      <li
                        key={`${step.agent_name ?? "unknown"}-${index}`}
                        className="rounded-[var(--radius-md)] border border-[var(--border)] p-3"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2 text-sm font-semibold">
                            <AgentIcon agentName={step.agent_name} />
                            <span>{step.execution_order ?? index + 1}.</span>
                            <span>{step.agent_name ?? "unknown_agent"}</span>
                          </div>
                          <StatusBadge status={status} />
                        </div>
                        <div className="mt-2 grid gap-2 text-xs text-[var(--text-muted)] md:grid-cols-3">
                          <p>Started: {formatDateTime(step.started_at)}</p>
                          <p>Ended: {formatDateTime(step.ended_at)}</p>
                          <p>Duration: {formatDurationMs(step.duration_ms)}</p>
                        </div>
                        {step.error ? (
                          <p className="mt-2 text-xs text-[var(--danger)]">
                            Error: {step.error}
                          </p>
                        ) : null}
                      </li>
                    );
                  })}
                </ol>
              )}
            </CardContent>
          </Card>

          {failedAgents.length > 0 ? (
            <Card className="border-[var(--danger)]/40">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg text-[var(--danger)]">
                  <AlertTriangle className="h-[var(--icon-md)] w-[var(--icon-md)]" />
                  Failure Isolation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="text-[var(--text-muted)]">
                  Some agents failed, but successful agent results are still available below.
                </p>
                <ul className="space-y-1">
                  {failedAgents.map((failed, index) => (
                    <li key={`${failed.agent_name ?? "failed"}-${index}`}>
                      <span className="font-semibold">
                        {failed.agent_name ?? "unknown_agent"}:
                      </span>{" "}
                      {agentErrorText(failed)}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
            <ResultCardShell
              title="Health Result"
              agentName="health_agent"
              status={toDisplayStatus(healthAgent?.status)}
            >
              {toDisplayStatus(healthAgent?.status) === "FAILED" ? (
                <p className="text-[var(--danger)]">{agentErrorText(healthAgent)}</p>
              ) : healthData ? (
                <>
                  <p>
                    Score: <span className="font-semibold">{`${healthData.overall_score ?? "-"}`}</span>
                    {" "}
                    Grade: <span className="font-semibold">{`${healthData.grade ?? "-"}`}</span>
                  </p>
                  <p className="text-[var(--text-muted)]">
                    {`${healthData.ai_explanation ?? "No health explanation available."}`}
                  </p>
                </>
              ) : (
                <p className="text-[var(--text-muted)]">No health payload returned.</p>
              )}
            </ResultCardShell>

            <ResultCardShell
              title="Spending Insights"
              agentName="insights_agent"
              status={toDisplayStatus(insightsAgent?.status)}
            >
              {toDisplayStatus(insightsAgent?.status) === "FAILED" ? (
                <p className="text-[var(--danger)]">{agentErrorText(insightsAgent)}</p>
              ) : insightsData ? (
                <>
                  <p className="font-semibold">
                    {`${(isRecord(insightsData.insights) && typeof insightsData.insights.summary === "string"
                      ? insightsData.insights.summary
                      : "No insights summary available.")}`}
                  </p>
                  <p>
                    Transactions: {`${(isRecord(insightsData.deterministic_summary) ? insightsData.deterministic_summary.transaction_count : "-") ?? "-"}`}
                  </p>
                </>
              ) : (
                <p className="text-[var(--text-muted)]">No insights payload returned.</p>
              )}
            </ResultCardShell>

            <ResultCardShell
              title="Budget"
              agentName="budget_agent"
              status={toDisplayStatus(budgetAgent?.status)}
            >
              {toDisplayStatus(budgetAgent?.status) === "FAILED" ? (
                <p className="text-[var(--danger)]">{agentErrorText(budgetAgent)}</p>
              ) : budgetData ? (
                <>
                  <p>
                    Potential savings: <span className="font-semibold">{`${budgetData.overall_potential_savings ?? "-"}`}</span>
                  </p>
                  <p className="text-[var(--text-muted)]">
                    {`${budgetData.ai_summary ?? "No budget summary available."}`}
                  </p>
                </>
              ) : (
                <p className="text-[var(--text-muted)]">No budget payload returned.</p>
              )}
            </ResultCardShell>

            <ResultCardShell
              title="Monthly Report"
              agentName="report_agent"
              status={toDisplayStatus(reportAgent?.status)}
            >
              {toDisplayStatus(reportAgent?.status) === "FAILED" ? (
                <p className="text-[var(--danger)]">{agentErrorText(reportAgent)}</p>
              ) : reportData ? (
                <>
                  <p className="font-semibold">
                    {`${reportData.executive_summary ?? "No executive summary available."}`}
                  </p>
                  <p>
                    Action items: {`${Array.isArray(reportData.action_plan) ? reportData.action_plan.length : 0}`}
                  </p>
                </>
              ) : (
                <p className="text-[var(--text-muted)]">No report payload returned.</p>
              )}
            </ResultCardShell>

            <ResultCardShell
              title="Assistant"
              agentName="assistant_agent"
              status={toDisplayStatus(assistantAgent?.status)}
            >
              {toDisplayStatus(assistantAgent?.status) === "FAILED" ? (
                <>
                  <p className="text-[var(--danger)]">{agentErrorText(assistantAgent)}</p>
                  <p className="text-[var(--text-muted)]">
                    Other completed agents remain available for judging review.
                  </p>
                </>
              ) : assistantData ? (
                <>
                  <p className="font-semibold">{`${assistantData.answer ?? "No assistant answer returned."}`}</p>
                  <p>
                    Confidence: {`${assistantData.confidence ?? "-"}`} • Sources:{" "}
                    {`${Array.isArray(assistantData.sources) ? assistantData.sources.length : 0}`}
                  </p>
                </>
              ) : (
                <p className="text-[var(--text-muted)]">No assistant payload returned.</p>
              )}
            </ResultCardShell>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Workflow Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>
                  Workflow: <span className="font-semibold">{formatUnknown(coordinatorData.metadata?.workflow_name, "-")}</span>
                </p>
                <p>
                  Successful: <span className="font-semibold">{formatUnknown(coordinatorData.metadata?.successful_agent_count, "0")}</span>
                  {" "}
                  Failed: <span className="font-semibold">{formatUnknown(coordinatorData.metadata?.failed_agent_count, "0")}</span>
                </p>
                <p>
                  Runner integrated: <span className="font-semibold">{formatUnknown(coordinatorData.metadata?.runner_integrated, "false")}</span>
                </p>
                <p>
                  Strategy: <span className="font-semibold">{formatUnknown(isRecord(coordinatorData.metadata?.workflow) ? coordinatorData.metadata?.workflow.strategy : undefined, "-")}</span>
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Technical Details</CardTitle>
            </CardHeader>
            <CardContent>
              <details>
                <summary className="cursor-pointer text-sm font-medium text-[var(--text-muted)]">
                  Show raw coordinator JSON
                </summary>
                <pre className="mt-3 max-h-[420px] overflow-auto rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3 text-xs leading-relaxed text-[var(--text)]">
                  {JSON.stringify(responsePayload, null, 2)}
                </pre>
              </details>
            </CardContent>
          </Card>
        </section>
      ) : null}

      {executionToast ? (
        <ExecutionToast
          toast={executionToast}
          onDismiss={dismissExecutionToast}
          onViewResults={() => {
            scrollToResults();
            dismissExecutionToast();
          }}
        />
      ) : null}
    </div>
  );
}
