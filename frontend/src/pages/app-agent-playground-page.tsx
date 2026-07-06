import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, LoaderCircle, Play } from "lucide-react";

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

const DEFAULT_SESSION_ID = "walletmind-session";

type FriendlyErrorState = {
  title: string;
  description: string;
};

function formatStatementOption(statement: UploadedStatement): string {
  const uploadedDate = new Date(statement.uploaded_at).toLocaleDateString();
  const status = statement.analysis_status.replace(/_/g, " ");
  return `${statement.original_filename} • ${uploadedDate} • ${status}`;
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

export function AppAgentPlaygroundPage() {
  const storedUser = getStoredUser();
  const [query, setQuery] = useState("");
  const [executionMode, setExecutionMode] = useState<AgentExecutionMode>(
    executionModeSchema.enum.single,
  );
  const [sessionId, setSessionId] = useState(DEFAULT_SESSION_ID);

  const [users, setUsers] = useState<WalletMindUser[]>([]);
  const [selectedUserUuid, setSelectedUserUuid] = useState(storedUser?.id ?? "");
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);

  const [statements, setStatements] = useState<UploadedStatement[]>([]);
  const [selectedStatementUuid, setSelectedStatementUuid] = useState("");
  const [statementsLoading, setStatementsLoading] = useState(false);
  const [statementsError, setStatementsError] = useState<string | null>(null);

  const [isExecuting, setIsExecuting] = useState(false);
  const [responsePayload, setResponsePayload] = useState<unknown | null>(null);
  const [executionError, setExecutionError] = useState<FriendlyErrorState | null>(
    null,
  );

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

        setUsersError("Unable to load users right now. Please refresh and retry.");
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

        setStatements(response);
        setSelectedStatementUuid((previous) => {
          if (previous && response.some((statement) => statement.statement_uuid === previous)) {
            return previous;
          }
          return response[0]?.statement_uuid ?? "";
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

  return (
    <div className="space-y-6">
      <PageTitle
        title="Agent Playground"
        subtitle="Interact directly with WalletMind's ADK-powered multi-agent system."
      />

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
                  onChange={() => setExecutionMode(executionModeSchema.enum.single)}
                />
                Single Agent
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="execution-mode"
                  checked={executionMode === executionModeSchema.enum.multi}
                  onChange={() => setExecutionMode(executionModeSchema.enum.multi)}
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
                  Executing Agents...
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

      {responsePayload ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Raw Coordinator Response</CardTitle>
          </CardHeader>
          <CardContent>
            <details>
              <summary className="cursor-pointer text-sm font-medium text-[var(--text-muted)]">
                Toggle raw JSON
              </summary>
              <pre className="mt-3 max-h-[420px] overflow-auto rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3 text-xs leading-relaxed text-[var(--text)]">
                {JSON.stringify(responsePayload, null, 2)}
              </pre>
            </details>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
