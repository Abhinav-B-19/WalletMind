import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";
import {
  BudgetCategoryCard,
  BudgetChart,
  BudgetComparisonTable,
  BudgetHeroCard,
  LoadingSkeleton,
  RecommendationPanel,
  SavingsOpportunityCard,
} from "@/features/ai-dashboard/components/budget";
import { EmptyStateCard } from "@/features/ai-dashboard/components/empty-state-card";
import { ErrorCard } from "@/features/ai-dashboard/components/error-card";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import {
  useBudgetRecommendations,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";
import { isAIUnavailableError } from "@/features/ai-dashboard/services/ai-degradation";
import type { BudgetRecommendation } from "@/features/ai-dashboard/types";
import { getStoredUser } from "@/lib/auth/storage";

type BudgetRow = {
  category: string;
  current: number;
  recommended: number;
  difference: number;
  variancePercent: number;
  status: "within" | "near" | "over";
  potentialSaving: number;
};

function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function toBudgetStatus(
  current: number,
  recommended: number,
): BudgetRow["status"] {
  if (recommended <= 0 || current <= recommended) {
    return "within";
  }
  if (current <= recommended * 1.1) {
    return "near";
  }
  return "over";
}

function toHealthBadge(
  rows: BudgetRow[],
): "Within Budget" | "Near Limit" | "Over Budget" {
  const overCount = rows.filter((row) => row.status === "over").length;
  const nearCount = rows.filter((row) => row.status === "near").length;

  if (overCount > 0) {
    return "Over Budget";
  }
  if (nearCount > 0) {
    return "Near Limit";
  }
  return "Within Budget";
}

function sortRecommendations(
  recommendations: BudgetRecommendation[],
): BudgetRecommendation[] {
  return [...recommendations].sort(
    (left, right) =>
      right.estimated_monthly_saving - left.estimated_monthly_saving,
  );
}

export function BudgetRecommendationsPage() {
  const user = getStoredUser();
  const currencyCode = user?.currency ?? "USD";
  const [searchParams] = useSearchParams();
  const statementFromQuery = searchParams.get("statement_id");
  const [selectedStatementUuid, setSelectedStatementUuid] = useState<
    string | null
  >(statementFromQuery);

  const statementsQuery = useProcessedStatements(user?.id);

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

  const budgetQuery = useBudgetRecommendations(selectedStatementUuid);
  const aiUnavailable =
    budgetQuery.isError && isAIUnavailableError(budgetQuery.error);

  const generatedAtLabel = useMemo(() => {
    if (!budgetQuery.dataUpdatedAt) {
      return "Pending";
    }

    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(budgetQuery.dataUpdatedAt));
  }, [budgetQuery.dataUpdatedAt]);

  const rows = useMemo<BudgetRow[]>(() => {
    if (!budgetQuery.data) {
      return [];
    }

    return Object.entries(budgetQuery.data.monthly_budget)
      .map(([category, values]) => {
        const current = values.historical;
        const recommended = values.recommended;
        const difference = current - recommended;
        const variancePercent =
          recommended <= 0 ? 0 : Math.min((current / recommended) * 100, 180);

        return {
          category,
          current,
          recommended,
          difference,
          variancePercent,
          status: toBudgetStatus(current, recommended),
          potentialSaving: values.potential_saving,
        };
      })
      .sort((left, right) => right.current - left.current);
  }, [budgetQuery.data]);

  const totalCurrentSpending = useMemo(
    () => rows.reduce((total, row) => total + row.current, 0),
    [rows],
  );

  const totalRecommendedSpending = useMemo(
    () => rows.reduce((total, row) => total + row.recommended, 0),
    [rows],
  );

  const overSpendingRows = useMemo(
    () =>
      rows
        .filter((row) => row.current > row.recommended)
        .sort((left, right) => right.difference - left.difference),
    [rows],
  );

  const sortedOpportunities = useMemo(
    () =>
      budgetQuery.data
        ? sortRecommendations(budgetQuery.data.priority_recommendations)
        : [],
    [budgetQuery.data],
  );

  const chartData = useMemo(() => {
    let running = 0;
    return rows.slice(0, 8).map((row) => {
      running += Math.max(0, row.potentialSaving);
      return {
        category: row.category,
        current: row.current,
        recommended: row.recommended,
        savings: Math.max(0, row.potentialSaving),
        runningSavings: running,
      };
    });
  }, [rows]);

  const budgetHealth = useMemo(() => toHealthBadge(rows), [rows]);

  const emergencyFundProgress = useMemo(() => {
    if (!budgetQuery.data || totalRecommendedSpending <= 0) {
      return 0;
    }

    const monthlyCoverageRatio =
      budgetQuery.data.overall_potential_savings / totalRecommendedSpending;
    return Math.min(100, Math.max(0, monthlyCoverageRatio * 100));
  }, [budgetQuery.data, totalRecommendedSpending]);

  if (statementsQuery.isLoading) {
    return (
      <div className="space-y-6" aria-label="Budget recommendations loading">
        <PageTitle
          title="Budget Recommendations"
          subtitle="Loading your budgeting intelligence workspace."
        />
        <LoadingSkeleton />
      </div>
    );
  }

  if (statementsQuery.isError) {
    return (
      <div className="space-y-6" aria-label="Budget recommendations error">
        <PageTitle
          title="Budget Recommendations"
          subtitle="Interactive dashboard for deterministic budget optimization."
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
      <div
        className="space-y-6"
        aria-label="Budget recommendations empty state"
      >
        <PageTitle
          title="Budget Recommendations"
          subtitle="Interactive dashboard for deterministic budget optimization."
        />
        <EmptyStateCard
          title="No Processed Statement Found"
          description="Upload and process a statement to unlock budget recommendations and savings opportunities."
          ctaLabel="Upload Statement"
          ctaHref="/app/statements/upload"
          ariaLabel="No processed statements for budget recommendations"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6" aria-label="Budget recommendations page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageTitle
          title="Budget Recommendations"
          subtitle="Transform deterministic budget analysis into actionable monthly savings decisions."
        />
        <Button asChild variant="secondary">
          <Link to="/app/dashboard">Back to AI Dashboard</Link>
        </Button>
      </div>

      <SectionCard
        title="Statement Context"
        description="Select a processed statement to refresh budget intelligence."
        action={<Badge variant="muted">Live</Badge>}
      >
        <label className="space-y-2" htmlFor="budget-statement-selector">
          <span className="text-sm text-[var(--text-muted)]">Statement</span>
          <select
            id="budget-statement-selector"
            aria-label="Budget statement selector"
            className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm"
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
          </select>
        </label>
      </SectionCard>

      {budgetQuery.isLoading ? <LoadingSkeleton /> : null}

      {budgetQuery.isError && !budgetQuery.data && !aiUnavailable ? (
        <ErrorCard
          title="Budget recommendations unavailable"
          message={
            budgetQuery.error instanceof Error
              ? budgetQuery.error.message
              : "Unable to load budget recommendations."
          }
          onRetry={() => void budgetQuery.refetch()}
        />
      ) : null}

      {budgetQuery.data ? (
        <>
          <BudgetHeroCard
            potentialSavings={formatCurrency(
              budgetQuery.data.overall_potential_savings,
              currencyCode,
            )}
            budgetHealth={budgetHealth}
            aiSummary={budgetQuery.data.ai_summary}
            generatedAt={generatedAtLabel}
          />

          <section
            className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
            aria-label="Budget overview cards"
          >
            <BudgetCategoryCard
              title="Current Spending"
              value={formatCurrency(totalCurrentSpending, currencyCode)}
              subtitle="Total monthly spend observed in statement data"
              tone="red"
            />
            <BudgetCategoryCard
              title="Recommended Budget"
              value={formatCurrency(totalRecommendedSpending, currencyCode)}
              subtitle="Optimized monthly budget target"
              tone="neutral"
            />
            <BudgetCategoryCard
              title="Potential Savings"
              value={formatCurrency(
                budgetQuery.data.overall_potential_savings,
                currencyCode,
              )}
              subtitle="Estimated monthly impact"
              tone="green"
            />
            <BudgetCategoryCard
              title="Emergency Fund Progress"
              value={`${emergencyFundProgress.toFixed(0)}%`}
              subtitle="One-month recommended budget coverage from savings"
              tone={
                emergencyFundProgress >= 75
                  ? "green"
                  : emergencyFundProgress >= 40
                    ? "yellow"
                    : "red"
              }
            />
          </section>

          <SectionCard
            title="Budget Comparison Table"
            description="Category-by-category current spend versus recommendation."
          >
            <BudgetComparisonTable
              rows={rows}
              currencyFormatter={(value) => formatCurrency(value, currencyCode)}
            />
          </SectionCard>

          <section
            className="grid gap-4 xl:grid-cols-2"
            aria-label="Overspending and savings opportunities"
          >
            <SectionCard
              title="Overspending Categories"
              description="Categories currently exceeding recommended budgets."
            >
              {overSpendingRows.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  Great work. No categories are currently above recommendation.
                </p>
              ) : (
                <div className="space-y-3">
                  {overSpendingRows.map((row) => (
                    <div
                      key={row.category}
                      className="rounded-[var(--radius-md)] border border-[#ff6a82]/30 bg-[#ff6a82]/10 p-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="text-sm font-semibold">
                          {row.category}
                        </h3>
                        <Badge
                          variant="muted"
                          className="bg-[#ff6a82]/20 text-[#ff6a82]"
                        >
                          Priority
                        </Badge>
                      </div>
                      <div className="mt-2 grid gap-2 text-sm text-[var(--text-muted)] sm:grid-cols-3">
                        <p>
                          Current: {formatCurrency(row.current, currencyCode)}
                        </p>
                        <p>
                          Recommended:{" "}
                          {formatCurrency(row.recommended, currencyCode)}
                        </p>
                        <p>
                          Variance:{" "}
                          {formatCurrency(row.difference, currencyCode)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard
              title="Savings Opportunities"
              description="Highest-impact opportunities sorted by estimated monthly savings."
            >
              {sortedOpportunities.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  No prioritized savings opportunities are currently available.
                </p>
              ) : (
                <div
                  className="grid gap-3"
                  aria-label="Savings opportunities list"
                >
                  {sortedOpportunities.map((item) => (
                    <SavingsOpportunityCard
                      key={`${item.title}-${item.category}`}
                      title={item.title}
                      category={item.category}
                      priority={item.priority}
                      estimatedSaving={formatCurrency(
                        item.estimated_monthly_saving,
                        currencyCode,
                      )}
                    />
                  ))}
                </div>
              )}
            </SectionCard>
          </section>

          <BudgetChart data={chartData} />

          <RecommendationPanel
            recommendations={budgetQuery.data.ai_recommendations}
            aiUnavailable={aiUnavailable}
            onRetry={() => void budgetQuery.refetch()}
          />

          {aiUnavailable ? (
            <p
              className="text-sm text-[var(--text-muted)]"
              aria-label="AI unavailable deterministic notice"
            >
              AI guidance is temporarily unavailable. Deterministic budget data
              remains visible.
            </p>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
