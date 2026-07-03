import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  CircleDollarSign,
  Landmark,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { PageTitle } from "@/components/ui/section-title";
import { getStoredUser } from "@/lib/auth/storage";
import { AIHeroCard } from "@/features/ai-dashboard/components/ai-hero-card";
import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";
import { EmptyStateCard } from "@/features/ai-dashboard/components/empty-state-card";
import { ErrorCard } from "@/features/ai-dashboard/components/error-card";
import { InsightCard } from "@/features/ai-dashboard/components/insight-card";
import { LoadingCard } from "@/features/ai-dashboard/components/loading-card";
import { MetricCard } from "@/features/ai-dashboard/components/metric-card";
import { RecommendationCard } from "@/features/ai-dashboard/components/recommendation-card";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import {
  useAIHealth,
  useBudgetRecommendations,
  useHealthScore,
  useInsights,
  useMonthlyReport,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";
import { isAIUnavailableError } from "@/features/ai-dashboard/services/ai-degradation";

function toStatusLabel(status: string): string {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function asNumber(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return 0;
}

function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

export function AIDashboardPage() {
  const user = getStoredUser();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const statementFromQuery = searchParams.get("statement_id");
  const [selectedStatementUuid, setSelectedStatementUuid] = useState<
    string | null
  >(statementFromQuery);
  const [assistantQuestion, setAssistantQuestion] = useState("");

  const statementsQuery = useProcessedStatements(user?.id);
  const aiHealthQuery = useAIHealth();

  useEffect(() => {
    if (
      !selectedStatementUuid &&
      statementsQuery.data &&
      statementsQuery.data.length > 0
    ) {
      setSelectedStatementUuid(statementsQuery.data[0].statement_uuid);
    }
  }, [selectedStatementUuid, statementsQuery.data]);

  useEffect(() => {
    if (statementFromQuery) {
      setSelectedStatementUuid(statementFromQuery);
    }
  }, [statementFromQuery]);

  const selectedStatement = useMemo(
    () =>
      statementsQuery.data?.find(
        (statement) => statement.statement_uuid === selectedStatementUuid,
      ) ?? null,
    [selectedStatementUuid, statementsQuery.data],
  );
  const activeStatementUuid = selectedStatement?.statement_uuid ?? null;

  const healthScoreQuery = useHealthScore(activeStatementUuid);
  const insightsQuery = useInsights(activeStatementUuid);
  const budgetQuery = useBudgetRecommendations(activeStatementUuid);
  const monthlyReportQuery = useMonthlyReport(activeStatementUuid);

  const insightsAIUnavailable =
    insightsQuery.isError && isAIUnavailableError(insightsQuery.error);
  const budgetAIUnavailable =
    budgetQuery.isError && isAIUnavailableError(budgetQuery.error);
  const monthlyReportAIUnavailable =
    monthlyReportQuery.isError &&
    isAIUnavailableError(monthlyReportQuery.error);

  const currencyCode = user?.currency || "USD";

  const quickMetrics = useMemo(() => {
    const report = monthlyReportQuery.data;
    if (!report) {
      return {
        income: 0,
        expenses: 0,
        savings: 0,
        cashFlow: 0,
      };
    }

    const income = asNumber(report.income_summary.total_income);
    const expenses = asNumber(report.expense_summary.total_expenses);
    const cashFlow = asNumber(report.cash_flow.net_cash_flow);
    const savings = Math.max(income - expenses, 0);

    return {
      income,
      expenses,
      savings,
      cashFlow,
    };
  }, [monthlyReportQuery.data]);

  const refreshDashboard = async () => {
    await queryClient.invalidateQueries({ queryKey: ["ai-dashboard"] });
  };

  if (statementsQuery.isLoading) {
    return (
      <div className="space-y-6" aria-label="AI dashboard loading">
        <PageTitle
          title="AI Dashboard"
          subtitle="Loading statement intelligence and concierge insights..."
        />
        <LoadingCard ariaLabel="Loading dashboard statements" lines={4} />
      </div>
    );
  }

  if (statementsQuery.isError) {
    return (
      <div className="space-y-6" aria-label="AI dashboard statement error">
        <PageTitle
          title="AI Dashboard"
          subtitle="The AI Financial Concierge workspace for your processed statements."
        />
        <ErrorCard
          title="Unable to load processed statements"
          message={
            statementsQuery.error instanceof Error
              ? statementsQuery.error.message
              : "Please retry to continue."
          }
          onRetry={() => void statementsQuery.refetch()}
        />
      </div>
    );
  }

  if (!statementsQuery.data || statementsQuery.data.length === 0) {
    return (
      <div className="space-y-6" aria-label="AI dashboard empty state">
        <PageTitle
          title="AI Dashboard"
          subtitle="The AI Financial Concierge workspace for your processed statements."
        />
        <EmptyStateCard
          title="No Processed Statement Found"
          description="Upload and process a statement first to unlock health score, AI insights, budget recommendations, and your monthly report."
          ctaLabel="Upload Statement"
          ctaHref="/app/statements/upload"
          ariaLabel="No processed statement"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6" aria-label="AI dashboard page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageTitle
          title="AI Dashboard"
          subtitle="Your AI Financial Concierge for health score, insights, recommendations, and reporting."
        />

        <Button
          type="button"
          variant="secondary"
          onClick={() => void refreshDashboard()}
          aria-label="Refresh AI dashboard data"
        >
          <RefreshCw className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
          Refresh
        </Button>
      </div>

      <SectionCard
        title="Statement Context"
        description="Select a processed statement to drive all dashboard modules."
      >
        <div className="grid gap-3 md:grid-cols-[1fr_auto_auto] md:items-center">
          <label className="space-y-2" htmlFor="statement-selector">
            <span className="text-sm text-[var(--text-muted)]">Statement</span>
            <Select
              id="statement-selector"
              aria-label="Statement selector"
              value={selectedStatementUuid ?? ""}
              onChange={(event) => setSelectedStatementUuid(event.target.value)}
            >
              {statementsQuery.data.map((statement) => (
                <option
                  key={statement.statement_uuid}
                  value={statement.statement_uuid}
                >
                  {statement.original_filename}
                </option>
              ))}
            </Select>
          </label>

          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-sm">
            <p className="text-[var(--text-muted)]">Processing Status</p>
            <p className="font-medium">
              {selectedStatement
                ? toStatusLabel(selectedStatement.analysis_status)
                : "Unknown"}
            </p>
          </div>

          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-sm">
            <p className="text-[var(--text-muted)]">AI Service</p>
            <div className="inline-flex items-center gap-2 font-medium">
              <Activity className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              {aiHealthQuery.data
                ? `${aiHealthQuery.data.status} (${aiHealthQuery.data.model})`
                : "Checking"}
            </div>
          </div>
        </div>
      </SectionCard>

      {healthScoreQuery.isLoading ? (
        <LoadingCard ariaLabel="Loading health score card" lines={6} />
      ) : null}
      {healthScoreQuery.isError ? (
        <ErrorCard
          title="Health score unavailable"
          message={
            healthScoreQuery.error instanceof Error
              ? healthScoreQuery.error.message
              : "Unable to load health score."
          }
          onRetry={() => void healthScoreQuery.refetch()}
        />
      ) : null}
      {healthScoreQuery.data ? (
        <div className="space-y-3">
          <AIHeroCard
            data={healthScoreQuery.data}
            onAction={() => {
              const question = assistantQuestion.trim();
              const base = selectedStatementUuid
                ? `/app/chat?statement_id=${selectedStatementUuid}`
                : "/app/chat";
              const href = question
                ? `${base}&q=${encodeURIComponent(question)}`
                : base;
              navigate(href);
            }}
          />
          {selectedStatementUuid ? (
            <Button asChild variant="secondary" className="w-full sm:w-auto">
              <Link to={`/app/health?statement_id=${selectedStatementUuid}`}>
                Open Full Financial Health Experience
              </Link>
            </Button>
          ) : null}
        </div>
      ) : null}

      <section
        className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"
        aria-label="Quick metrics"
      >
        <MetricCard
          label="Income"
          value={formatCurrency(quickMetrics.income, currencyCode)}
          icon={TrendingUp}
          toneClassName="text-[#27c86f]"
        />
        <MetricCard
          label="Expenses"
          value={formatCurrency(quickMetrics.expenses, currencyCode)}
          icon={TrendingDown}
          toneClassName="text-[#ff6a82]"
        />
        <MetricCard
          label="Savings"
          value={formatCurrency(quickMetrics.savings, currencyCode)}
          icon={Landmark}
          toneClassName="text-[#e3be37]"
        />
        <MetricCard
          label="Cash Flow"
          value={formatCurrency(quickMetrics.cashFlow, currencyCode)}
          icon={CircleDollarSign}
          toneClassName="text-[#29d0b3]"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <SectionCard
          title="AI Insights Preview"
          description="Top spending insights generated for this statement."
          action={
            <Button asChild variant="secondary" size="sm">
              <Link
                to={
                  selectedStatementUuid
                    ? `/app/insights?statement_id=${selectedStatementUuid}`
                    : "/app/insights"
                }
              >
                View More
              </Link>
            </Button>
          }
        >
          {insightsQuery.isLoading ? (
            <LoadingCard ariaLabel="Loading AI insights" lines={4} compact />
          ) : null}
          {insightsQuery.isError && !insightsAIUnavailable ? (
            <ErrorCard
              title="Insights unavailable"
              message={
                insightsQuery.error instanceof Error
                  ? insightsQuery.error.message
                  : "Unable to load insights."
              }
              onRetry={() => void insightsQuery.refetch()}
            />
          ) : null}
          {insightsAIUnavailable ? (
            <AIUnavailableCard onRetry={() => void insightsQuery.refetch()} />
          ) : null}
          {insightsQuery.data ? (
            <>
              {!insightsAIUnavailable ? (
                <p className="text-sm text-[var(--text-muted)]">
                  {insightsQuery.data.insights.summary}
                </p>
              ) : null}
              <div className="grid gap-3">
                {!insightsAIUnavailable
                  ? insightsQuery.data.insights.recommendations
                      .slice(0, 3)
                      .map((insight) => (
                        <InsightCard
                          key={insight.title}
                          title={insight.title}
                          description={insight.description}
                          priority={insight.priority}
                        />
                      ))
                  : null}
              </div>
            </>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Budget Recommendation Preview"
          description="Focus recommendations with the highest immediate impact."
          action={
            <Button asChild variant="secondary" size="sm">
              <Link
                to={
                  selectedStatementUuid
                    ? `/app/budget?statement_id=${selectedStatementUuid}`
                    : "/app/budget"
                }
              >
                View More
              </Link>
            </Button>
          }
        >
          {budgetQuery.isLoading ? (
            <LoadingCard
              ariaLabel="Loading budget recommendations"
              lines={4}
              compact
            />
          ) : null}
          {budgetQuery.isError && !budgetAIUnavailable ? (
            <ErrorCard
              title="Budget recommendations unavailable"
              message={
                budgetQuery.error instanceof Error
                  ? budgetQuery.error.message
                  : "Unable to load recommendations."
              }
              onRetry={() => void budgetQuery.refetch()}
            />
          ) : null}
          {budgetAIUnavailable ? (
            <AIUnavailableCard onRetry={() => void budgetQuery.refetch()} />
          ) : null}
          {budgetQuery.data ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
                <p className="text-sm text-[var(--text-muted)]">
                  Potential Monthly Savings
                </p>
                <p className="text-xl font-semibold">
                  {formatCurrency(
                    budgetQuery.data.overall_potential_savings,
                    currencyCode,
                  )}
                </p>
              </div>
              {!budgetAIUnavailable ? (
                <p className="text-sm text-[var(--text-muted)]">
                  {budgetQuery.data.ai_summary}
                </p>
              ) : null}
              {budgetQuery.data.priority_recommendations[0] ? (
                <RecommendationCard
                  title={budgetQuery.data.priority_recommendations[0].title}
                  category={
                    budgetQuery.data.priority_recommendations[0].category
                  }
                  priority={
                    budgetQuery.data.priority_recommendations[0].priority
                  }
                  estimatedSaving={
                    budgetQuery.data.priority_recommendations[0]
                      .estimated_monthly_saving
                  }
                />
              ) : (
                <p className="text-sm text-[var(--text-muted)]">
                  No specific recommendation is currently available.
                </p>
              )}
            </>
          ) : null}
        </SectionCard>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <SectionCard
          title="Financial Assistant"
          description="Draft your next question, then open the assistant with statement context."
          action={
            <Badge variant="muted" className="uppercase">
              Concierge
            </Badge>
          }
        >
          <label
            htmlFor="assistant-question"
            className="text-sm text-[var(--text-muted)]"
          >
            Your question
          </label>
          <textarea
            id="assistant-question"
            value={assistantQuestion}
            onChange={(event) => setAssistantQuestion(event.target.value)}
            placeholder="Example: How can I reduce my grocery and dining costs next month?"
            className="min-h-28 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text)] outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
          />
          <Button asChild>
            <Link
              to={
                selectedStatementUuid
                  ? `/app/chat?statement_id=${selectedStatementUuid}`
                  : "/app/chat"
              }
              aria-label="Open AI assistant"
            >
              <Bot className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              Open Assistant
            </Link>
          </Button>
        </SectionCard>

        <SectionCard
          title="Monthly Report Preview"
          description="Executive monthly narrative built from deterministic analysis."
          action={
            <Button asChild variant="secondary" size="sm">
              <Link to="/app/planner">Open Full Report</Link>
            </Button>
          }
        >
          {monthlyReportQuery.isLoading ? (
            <LoadingCard ariaLabel="Loading monthly report" lines={5} compact />
          ) : null}
          {monthlyReportQuery.isError && !monthlyReportAIUnavailable ? (
            <ErrorCard
              title="Monthly report unavailable"
              message={
                monthlyReportQuery.error instanceof Error
                  ? monthlyReportQuery.error.message
                  : "Unable to load report."
              }
              onRetry={() => void monthlyReportQuery.refetch()}
            />
          ) : null}
          {monthlyReportAIUnavailable ? (
            <AIUnavailableCard
              onRetry={() => void monthlyReportQuery.refetch()}
            />
          ) : null}
          {monthlyReportQuery.data ? (
            <>
              {!monthlyReportAIUnavailable ? (
                <p className="text-sm text-[var(--text-muted)]">
                  {monthlyReportQuery.data.executive_summary}
                </p>
              ) : null}
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                    Health Grade
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {monthlyReportQuery.data.health_score.grade ?? "N/A"}
                  </p>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                    Risks
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {monthlyReportQuery.data.risks.length}
                  </p>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                    Action Plan
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {monthlyReportQuery.data.action_plan.length}
                  </p>
                </div>
              </div>
            </>
          ) : null}
        </SectionCard>
      </section>
    </div>
  );
}
