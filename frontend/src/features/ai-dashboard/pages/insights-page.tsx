import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";
import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";
import { EmptyStateCard } from "@/features/ai-dashboard/components/empty-state-card";
import { ErrorCard } from "@/features/ai-dashboard/components/error-card";
import {
  CashFlowChart,
  CategoryChart,
  InsightGrid,
  InsightHero,
  InsightTimeline,
  LoadingSkeleton,
  MerchantChart,
} from "@/features/ai-dashboard/components/insights";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import {
  useInsights,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";
import { isAIUnavailableError } from "@/features/ai-dashboard/services/ai-degradation";
import { getStoredUser } from "@/lib/auth/storage";

function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMonthLabel(month: string): string {
  const [year, numericMonth] = month.split("-");
  if (!year || !numericMonth) {
    return month;
  }

  const date = new Date(Number(year), Number(numericMonth) - 1, 1);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    year: "numeric",
  }).format(date);
}

function toConfidenceLabel(totalTokens: number, finishReason: string): string {
  const finishBonus = finishReason.toLowerCase() === "stop" ? 15 : 5;
  const tokenBonus = Math.min(20, Math.floor(totalTokens / 100));
  const score = Math.min(98, Math.max(55, 60 + finishBonus + tokenBonus));
  const tier = score >= 85 ? "High" : score >= 70 ? "Moderate" : "Review";
  return `${score}% (${tier})`;
}

export function InsightsPage() {
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

  const insightsQuery = useInsights(selectedStatementUuid);
  const aiUnavailable =
    insightsQuery.isError && isAIUnavailableError(insightsQuery.error);

  const confidenceLabel = useMemo(() => {
    if (!insightsQuery.data) {
      return "N/A";
    }

    return toConfidenceLabel(
      insightsQuery.data.total_tokens,
      insightsQuery.data.finish_reason,
    );
  }, [insightsQuery.data]);

  const generatedAtLabel = useMemo(() => {
    if (!insightsQuery.dataUpdatedAt) {
      return "Pending";
    }

    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(insightsQuery.dataUpdatedAt));
  }, [insightsQuery.dataUpdatedAt]);

  const chartData = useMemo(() => {
    if (!insightsQuery.data) {
      return {
        categoryData: [],
        paymentChannelData: [],
        merchantData: [],
        monthlyTrend: [],
      };
    }

    const summary = insightsQuery.data.deterministic_summary;

    const categoryData =
      summary.top_spending_categories.length > 0
        ? summary.top_spending_categories.map((item) => ({
            name: item.category,
            value: item.amount,
          }))
        : Object.entries(summary.category_breakdown)
            .slice(0, 5)
            .map(([name, value]) => ({ name, value }));

    const paymentChannelData = [
      { name: "Credit", value: summary.credit_count },
      { name: "Debit", value: summary.debit_count },
    ];

    const merchantData = summary.top_merchants.slice(0, 8);

    const monthlyTrend = summary.monthly_trend.map((item) => ({
      ...item,
      month: formatMonthLabel(item.month),
    }));

    return {
      categoryData,
      paymentChannelData,
      merchantData,
      monthlyTrend,
    };
  }, [insightsQuery.data]);

  const timelineItems = useMemo(() => {
    if (!insightsQuery.data) {
      return [];
    }

    return insightsQuery.data.deterministic_summary.monthly_trend.map(
      (point) => {
        const polarity = point.net >= 0 ? "positive" : "negative";
        const note =
          point.net >= 0
            ? `Net ${polarity} at ${formatCurrency(point.net, currencyCode)} with expenses at ${formatCurrency(point.expenses, currencyCode)}.`
            : `Net ${polarity} at ${formatCurrency(point.net, currencyCode)}. Expenses reached ${formatCurrency(point.expenses, currencyCode)}.`;

        return {
          month: formatMonthLabel(point.month),
          note,
        };
      },
    );
  }, [insightsQuery.data, currencyCode]);

  if (statementsQuery.isLoading) {
    return (
      <div className="space-y-6" aria-label="Insights page loading">
        <PageTitle
          title="Spending Insights"
          subtitle="Loading AI spending intelligence for your processed statements."
        />
        <LoadingSkeleton />
      </div>
    );
  }

  if (statementsQuery.isError) {
    return (
      <div className="space-y-6" aria-label="Insights page error">
        <PageTitle
          title="Spending Insights"
          subtitle="Interactive intelligence from your statement data."
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
      <div className="space-y-6" aria-label="Insights page empty state">
        <PageTitle
          title="Spending Insights"
          subtitle="Interactive intelligence from your statement data."
        />
        <EmptyStateCard
          title="No Processed Statement Found"
          description="Upload and process a statement to unlock category trends, merchant distribution, and AI insights."
          ctaLabel="Upload Statement"
          ctaHref="/app/statements/upload"
          ariaLabel="No processed statements for insights"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6" aria-label="Insights page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageTitle
          title="Spending Insights"
          subtitle="A modern AI insights dashboard built from deterministic and model-driven analysis."
        />
        <div className="flex gap-2">
          <Button asChild variant="secondary">
            <Link to="/app/dashboard">Back to AI Dashboard</Link>
          </Button>
        </div>
      </div>

      <SectionCard
        title="Statement Context"
        description="Select a processed statement to refresh all insight visualizations."
        action={<Badge variant="muted">Live</Badge>}
      >
        <label className="space-y-2" htmlFor="insight-statement-selector">
          <span className="text-sm text-[var(--text-muted)]">Statement</span>
          <select
            id="insight-statement-selector"
            aria-label="Insights statement selector"
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

      {insightsQuery.isLoading ? <LoadingSkeleton /> : null}

      {insightsQuery.isError && !aiUnavailable ? (
        <ErrorCard
          title="Insights unavailable"
          message={
            insightsQuery.error instanceof Error
              ? insightsQuery.error.message
              : "Unable to load spending insights."
          }
          onRetry={() => void insightsQuery.refetch()}
        />
      ) : null}

      {aiUnavailable ? (
        <AIUnavailableCard onRetry={() => void insightsQuery.refetch()} />
      ) : null}

      {insightsQuery.data ? (
        <>
          {!aiUnavailable ? (
            <InsightHero
              summary={insightsQuery.data.insights.summary}
              confidenceLabel={confidenceLabel}
              generatedAtLabel={generatedAtLabel}
            />
          ) : null}

          <SectionCard
            title="Key Insights"
            description="Core high-impact signals synthesized into actionable metrics."
          >
            <InsightGrid
              highSpending={
                insightsQuery.data.deterministic_summary.largest_expense
                  ? formatCurrency(
                      insightsQuery.data.deterministic_summary.largest_expense
                        .amount,
                      currencyCode,
                    )
                  : "N/A"
              }
              savingsOpportunity={`${insightsQuery.data.deterministic_summary.cash_flow.savings_rate.toFixed(1)}% Savings Rate`}
              largestMerchant={
                insightsQuery.data.deterministic_summary.top_merchants[0]
                  ? insightsQuery.data.deterministic_summary.top_merchants[0]
                      .merchant
                  : "N/A"
              }
              largestCategory={
                insightsQuery.data.deterministic_summary
                  .top_spending_categories[0]
                  ? insightsQuery.data.deterministic_summary
                      .top_spending_categories[0].category
                  : "N/A"
              }
              recurringPayments={String(
                insightsQuery.data.deterministic_summary.recurring_subscriptions
                  .length,
              )}
              subscriptions={
                insightsQuery.data.deterministic_summary
                  .recurring_subscriptions[0]
                  ? insightsQuery.data.deterministic_summary
                      .recurring_subscriptions[0].merchant
                  : "None detected"
              }
            />
          </SectionCard>

          <section
            className="grid gap-4 xl:grid-cols-2"
            aria-label="Insight charts"
          >
            <CategoryChart
              categoryData={chartData.categoryData}
              paymentChannelData={chartData.paymentChannelData}
            />
            <MerchantChart merchants={chartData.merchantData} />
          </section>

          <CashFlowChart monthlyTrend={chartData.monthlyTrend} />

          <InsightTimeline items={timelineItems} />

          <SectionCard
            title="Action Cards"
            description="Quick recommendations derived from the AI insight engine."
          >
            <div
              className="grid gap-3 md:grid-cols-2 xl:grid-cols-3"
              aria-label="Insight action cards"
            >
              {insightsQuery.data.insights.recommendations.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  No recommendations are currently available for this statement.
                </p>
              ) : (
                insightsQuery.data.insights.recommendations.map(
                  (recommendation) => (
                    <div
                      key={recommendation.title}
                      className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4"
                    >
                      <p className="mb-2 text-xs uppercase tracking-wide text-[var(--text-muted)]">
                        {recommendation.priority} priority
                      </p>
                      <h3 className="text-sm font-semibold">
                        {recommendation.title}
                      </h3>
                      <p className="mt-2 text-sm text-[var(--text-muted)]">
                        {recommendation.description}
                      </p>
                    </div>
                  ),
                )
              )}
            </div>
          </SectionCard>
        </>
      ) : null}
    </div>
  );
}
