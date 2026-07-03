import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";
import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";
import {
  BudgetChart,
  BudgetComparisonTable,
  SavingsOpportunityCard,
} from "@/features/ai-dashboard/components/budget";
import { EmptyStateCard } from "@/features/ai-dashboard/components/empty-state-card";
import { ErrorCard } from "@/features/ai-dashboard/components/error-card";
import {
  HealthMetricCard,
  RecommendationCard as HealthRecommendationCard,
  StrengthCard,
  WeaknessCard,
} from "@/features/ai-dashboard/components/financial-health";
import { HealthScoreGauge } from "@/features/ai-dashboard/components/health-score-gauge";
import {
  CashFlowChart,
  CategoryChart,
  InsightGrid,
  MerchantChart,
} from "@/features/ai-dashboard/components/insights";
import { LoadingCard } from "@/features/ai-dashboard/components/loading-card";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import {
  useBudgetRecommendations,
  useHealthScore,
  useInsights,
  useMonthlyReport,
  useProcessedStatements,
} from "@/features/ai-dashboard/hooks";
import { isAIUnavailableError } from "@/features/ai-dashboard/services/ai-degradation";
import type { BudgetRecommendation } from "@/features/ai-dashboard/types";
import { getStoredUser } from "@/lib/auth/storage";

const HEALTH_METRIC_LABELS: Record<string, string> = {
  savings_rate: "Savings Rate",
  income_stability: "Income Stability",
  spending_discipline: "Spending Discipline",
  recurring_obligations: "Recurring Obligations",
  cash_flow: "Cash Flow",
};

const HEALTH_METRIC_DESCRIPTIONS: Record<string, string> = {
  savings_rate: "How consistently your income turns into retained savings.",
  income_stability: "How predictable your earning pattern is month to month.",
  spending_discipline:
    "How closely actual spending aligns with healthy limits.",
  recurring_obligations: "How manageable fixed recurring obligations are.",
  cash_flow: "How consistently income exceeds expenses over time.",
};

type TrendPoint = {
  month: string;
  income: number;
  expenses: number;
  net: number;
};

type IncomeSource = {
  label: string;
  amount: number;
};

type RiskItem = {
  label: string;
  severity: "high" | "medium" | "low";
};

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

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }

  return value as Record<string, unknown>;
}

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

function formatDateTime(value: number): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function riskSeverity(text: string, index: number): RiskItem["severity"] {
  const normalized = text.toLowerCase();
  if (
    normalized.includes("overdraft") ||
    normalized.includes("debt") ||
    normalized.includes("high") ||
    normalized.includes("negative")
  ) {
    return "high";
  }

  if (normalized.includes("watch") || normalized.includes("rising")) {
    return "medium";
  }

  return index === 0 ? "medium" : "low";
}

function budgetPrioritySort(
  recommendations: BudgetRecommendation[],
): BudgetRecommendation[] {
  return [...recommendations].sort(
    (left, right) =>
      right.estimated_monthly_saving - left.estimated_monthly_saving,
  );
}

function toTrendPoints(value: unknown): TrendPoint[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => asRecord(item))
    .map((item) => ({
      month: formatMonthLabel(asString(item.month)),
      income: asNumber(item.income),
      expenses: asNumber(item.expenses),
      net: asNumber(item.net),
    }))
    .filter((item) => item.month.length > 0);
}

function toIncomeSources(value: unknown): IncomeSource[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => asRecord(item))
    .map((item) => ({
      label:
        asString(item.source) ||
        asString(item.merchant) ||
        asString(item.category) ||
        "Income Source",
      amount: asNumber(item.amount),
    }))
    .filter((item) => item.amount > 0)
    .slice(0, 4);
}

function toPaymentChannels(
  creditCount: number,
  debitCount: number,
): Array<{ name: string; value: number }> {
  return [
    { name: "Credit", value: creditCount },
    { name: "Debit", value: debitCount },
  ];
}

export function MonthlyFinancialReportPage() {
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

  const monthlyReportQuery = useMonthlyReport(selectedStatementUuid);
  const healthQuery = useHealthScore(selectedStatementUuid);
  const insightsQuery = useInsights(selectedStatementUuid);
  const budgetQuery = useBudgetRecommendations(selectedStatementUuid);

  const healthAIUnavailable =
    healthQuery.isError && isAIUnavailableError(healthQuery.error);
  const insightsAIUnavailable =
    insightsQuery.isError && isAIUnavailableError(insightsQuery.error);
  const budgetAIUnavailable =
    budgetQuery.isError && isAIUnavailableError(budgetQuery.error);
  const reportAIUnavailable =
    monthlyReportQuery.isError &&
    isAIUnavailableError(monthlyReportQuery.error);

  const generatedAtLabel = useMemo(() => {
    const source = monthlyReportQuery.dataUpdatedAt || Date.now();
    return formatDateTime(source);
  }, [monthlyReportQuery.dataUpdatedAt]);

  const report = monthlyReportQuery.data;
  const financialHealth = asRecord(report?.financial_health);
  const incomeSummary = asRecord(report?.income_summary);
  const expenseSummary = asRecord(report?.expense_summary);
  const cashFlowSummary = asRecord(report?.cash_flow);
  const spendingSummary = asRecord(report?.spending_insights);

  const healthScore = useMemo(() => {
    const reportHealth = asRecord(report?.health_score);
    const reportComponents = asRecord(reportHealth.components);

    return {
      overall_score:
        healthQuery.data?.overall_score ?? asNumber(reportHealth.overall_score),
      grade: healthQuery.data?.grade ?? (asString(reportHealth.grade) || "N/A"),
      components: healthQuery.data?.components ?? {
        savings_rate: asNumber(reportComponents.savings_rate),
        income_stability: asNumber(reportComponents.income_stability),
        spending_discipline: asNumber(reportComponents.spending_discipline),
        recurring_obligations: asNumber(reportComponents.recurring_obligations),
        cash_flow: asNumber(reportComponents.cash_flow),
      },
      strengths:
        healthQuery.data?.strengths ??
        asStringArray(financialHealth.strengths).concat(
          report?.strengths ?? [],
        ),
      weaknesses:
        healthQuery.data?.weaknesses ??
        asStringArray(financialHealth.weaknesses),
      recommendations:
        healthQuery.data?.recommendations ??
        asStringArray(financialHealth.recommendations),
    };
  }, [financialHealth, healthQuery.data, report]);

  const metrics = useMemo(
    () => [
      {
        key: "savings_rate",
        title: HEALTH_METRIC_LABELS.savings_rate,
        score: healthScore.components.savings_rate,
      },
      {
        key: "income_stability",
        title: HEALTH_METRIC_LABELS.income_stability,
        score: healthScore.components.income_stability,
      },
      {
        key: "spending_discipline",
        title: HEALTH_METRIC_LABELS.spending_discipline,
        score: healthScore.components.spending_discipline,
      },
      {
        key: "recurring_obligations",
        title: HEALTH_METRIC_LABELS.recurring_obligations,
        score: healthScore.components.recurring_obligations,
      },
      {
        key: "cash_flow",
        title: HEALTH_METRIC_LABELS.cash_flow,
        score: healthScore.components.cash_flow,
      },
    ],
    [healthScore.components],
  );

  const incomeTotals = useMemo(() => {
    const deterministic = insightsQuery.data?.deterministic_summary;

    return {
      totalIncome: (() => {
        const incomeFromSummary = asNumber(incomeSummary.total_income);
        if (incomeFromSummary > 0) {
          return incomeFromSummary;
        }
        return deterministic?.cash_flow.total_income ?? 0;
      })(),
      averageIncome:
        asNumber(incomeSummary.average_monthly_income) ||
        deterministic?.monthly_averages.income ||
        0,
      stabilityScore:
        healthScore.components.income_stability ||
        asNumber(incomeSummary.income_stability) ||
        0,
      largestIncome:
        deterministic?.largest_income?.amount ||
        asNumber(incomeSummary.largest_income),
      largestIncomeLabel:
        deterministic?.largest_income?.merchant ||
        asString(incomeSummary.largest_income_source),
      sources:
        toIncomeSources(incomeSummary.largest_income_sources) ||
        (deterministic?.largest_income
          ? [
              {
                label: deterministic.largest_income.merchant,
                amount: deterministic.largest_income.amount,
              },
            ]
          : []),
    };
  }, [
    healthScore.components.income_stability,
    incomeSummary,
    insightsQuery.data,
  ]);

  const expenseBreakdown = useMemo(() => {
    const deterministic = insightsQuery.data?.deterministic_summary;
    const topCategories = deterministic?.top_spending_categories ?? [];
    const categoryDistribution =
      topCategories.length > 0
        ? topCategories.map((item) => ({
            name: item.category,
            value: item.amount,
          }))
        : Object.entries(asRecord(expenseSummary.category_distribution)).map(
            ([name, value]) => ({ name, value: asNumber(value) }),
          );

    return {
      totalExpenses:
        asNumber(expenseSummary.total_expenses) ||
        deterministic?.cash_flow.total_expenses ||
        0,
      largestExpense:
        deterministic?.largest_expense?.amount ||
        asNumber(expenseSummary.largest_expense),
      largestExpenseLabel:
        deterministic?.largest_expense?.merchant ||
        asString(expenseSummary.largest_expense_merchant),
      merchants: deterministic?.top_merchants ?? [],
      categoryDistribution: categoryDistribution.slice(0, 8),
      paymentChannels: toPaymentChannels(
        deterministic?.credit_count ?? asNumber(expenseSummary.credit_count),
        deterministic?.debit_count ?? asNumber(expenseSummary.debit_count),
      ),
    };
  }, [expenseSummary, insightsQuery.data]);

  const trendPoints = useMemo(() => {
    const deterministic =
      insightsQuery.data?.deterministic_summary.monthly_trend;
    if (deterministic && deterministic.length > 0) {
      return deterministic.map((item) => ({
        month: formatMonthLabel(item.month),
        income: item.income,
        expenses: item.expenses,
        net: item.net,
      }));
    }

    return toTrendPoints(cashFlowSummary.monthly_trend);
  }, [cashFlowSummary.monthly_trend, insightsQuery.data]);

  const budgetRows = useMemo(() => {
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
          status:
            recommended <= 0 || current <= recommended
              ? ("within" as const)
              : current <= recommended * 1.1
                ? ("near" as const)
                : ("over" as const),
          potentialSaving: values.potential_saving,
        };
      })
      .sort((left, right) => right.current - left.current);
  }, [budgetQuery.data]);

  const budgetChartData = useMemo(() => {
    let running = 0;
    return budgetRows.slice(0, 8).map((row) => {
      running += Math.max(0, row.potentialSaving);
      return {
        category: row.category,
        current: row.current,
        recommended: row.recommended,
        savings: Math.max(0, row.potentialSaving),
        runningSavings: running,
      };
    });
  }, [budgetRows]);

  const topRisks = useMemo<RiskItem[]>(() => {
    const riskText = report?.risks ?? [];
    return riskText.slice(0, 4).map((item, index) => ({
      label: item,
      severity: riskSeverity(item, index),
    }));
  }, [report]);

  const topActions = useMemo(() => {
    const budgetPriorityActions = budgetPrioritySort(
      budgetQuery.data?.priority_recommendations ?? [],
    ).slice(0, 3);

    if (budgetPriorityActions.length > 0) {
      return budgetPriorityActions.map((item) => ({
        title: item.title,
        priority: item.priority,
        category: item.category,
        savings: item.estimated_monthly_saving,
      }));
    }

    return (report?.action_plan ?? []).slice(0, 3).map((item, index) => ({
      title: item,
      priority: index === 0 ? "high" : index === 1 ? "medium" : "low",
      category: "General",
      savings: 0,
    }));
  }, [budgetQuery.data?.priority_recommendations, report]);

  if (statementsQuery.isLoading) {
    return (
      <div className="space-y-6" aria-label="Monthly report page loading">
        <PageTitle
          title="Monthly Financial Report"
          subtitle="Preparing your premium advisor-grade monthly report."
        />
        <LoadingCard ariaLabel="Loading monthly report cover" lines={6} />
        <LoadingCard ariaLabel="Loading monthly report sections" lines={5} />
        <LoadingCard ariaLabel="Loading monthly report sections" lines={5} />
      </div>
    );
  }

  if (statementsQuery.isError) {
    return (
      <div
        className="space-y-6"
        aria-label="Monthly report page statement error"
      >
        <PageTitle
          title="Monthly Financial Report"
          subtitle="Your flagship advisor-grade summary, built from statement intelligence."
        />
        <ErrorCard
          title="Unable to load processed statements"
          message="Unable to fetch statement context right now. Please retry."
          onRetry={() => void statementsQuery.refetch()}
        />
      </div>
    );
  }

  if (!statementsQuery.data || statementsQuery.data.length === 0) {
    return (
      <div className="space-y-6" aria-label="Monthly report page empty state">
        <PageTitle
          title="Monthly Financial Report"
          subtitle="Your flagship advisor-grade summary, built from statement intelligence."
        />
        <EmptyStateCard
          title="No Processed Statement Found"
          description="Upload and process a statement to generate your monthly financial report."
          ctaLabel="Upload Statement"
          ctaHref="/app/statements/upload"
          ariaLabel="No processed statements for monthly report"
        />
      </div>
    );
  }

  if (monthlyReportQuery.isLoading && !report) {
    return (
      <div className="space-y-6" aria-label="Monthly report loading sections">
        <PageTitle
          title="Monthly Financial Report"
          subtitle="Preparing your premium advisor-grade monthly report."
        />
        <LoadingCard ariaLabel="Loading report cover section" lines={7} />
        <div className="grid gap-4 xl:grid-cols-2">
          <LoadingCard ariaLabel="Loading report section" lines={6} />
          <LoadingCard ariaLabel="Loading report section" lines={6} />
        </div>
        <LoadingCard ariaLabel="Loading report chart section" lines={8} />
      </div>
    );
  }

  if (monthlyReportQuery.isError && !report && !reportAIUnavailable) {
    return (
      <div className="space-y-6" aria-label="Monthly report page error">
        <PageTitle
          title="Monthly Financial Report"
          subtitle="Your flagship advisor-grade summary, built from statement intelligence."
        />
        <ErrorCard
          title="Monthly report unavailable"
          message="Report generation is temporarily unavailable. Please retry in a moment."
          onRetry={() => void monthlyReportQuery.refetch()}
        />
      </div>
    );
  }

  if (!report) {
    return null;
  }

  const totalIncome = incomeTotals.totalIncome;
  const totalExpenses = expenseBreakdown.totalExpenses;
  const netCashFlow =
    asNumber(cashFlowSummary.net_cash_flow) || totalIncome - totalExpenses;
  const savingsRate =
    asNumber(cashFlowSummary.savings_rate) ||
    (totalIncome > 0 ? (netCashFlow / totalIncome) * 100 : 0);

  return (
    <div
      className="space-y-6 print:space-y-4"
      aria-label="Monthly financial report page"
      data-testid="monthly-report-root"
    >
      <div className="flex flex-wrap items-start justify-between gap-4 print:hidden">
        <PageTitle
          title="Monthly Financial Report"
          subtitle="Advisor-grade monthly intelligence with actionable plan and savings impact."
        />
        <Button asChild variant="secondary">
          <Link to="/app/dashboard">Back to AI Dashboard</Link>
        </Button>
      </div>

      <SectionCard
        title="Report Cover"
        description="Professional monthly briefing generated from deterministic and AI-assisted analysis."
        className="break-inside-avoid"
        action={<Badge variant="muted">Flagship Report</Badge>}
      >
        <div
          className="grid gap-4 xl:grid-cols-[1.3fr_1fr]"
          aria-label="Report cover layout"
        >
          <div className="space-y-3">
            <p className="text-sm text-[var(--text-muted)]">
              {report.executive_summary}
            </p>
            <div className="grid gap-2 text-sm text-[var(--text-muted)] sm:grid-cols-2">
              <p>Statement: {selectedStatementUuid ?? "N/A"}</p>
              <p>Generated: {generatedAtLabel}</p>
              <p>Period: Monthly statement intelligence snapshot</p>
              <p>Financial Health Grade: {healthScore.grade}</p>
            </div>
          </div>
          <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-soft)] p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                Overall Score
              </p>
              <Badge variant="muted">{healthScore.grade}</Badge>
            </div>
            <div className="mt-3 flex items-center justify-center">
              <HealthScoreGauge
                score={healthScore.overall_score}
                grade={healthScore.grade}
              />
            </div>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Executive Summary"
        description="Concise financial snapshot with achievement and concern highlights."
        className="break-inside-avoid"
      >
        <div
          className="grid gap-4 xl:grid-cols-[1.5fr_1fr]"
          aria-label="Executive summary layout"
        >
          <div className="rounded-[var(--radius-lg)] border border-[#4f8df7]/25 bg-[#4f8df7]/10 p-4">
            <p className="text-sm leading-relaxed">
              {report.executive_summary}
            </p>
          </div>
          <div className="grid gap-3">
            <div className="rounded-[var(--radius-md)] border border-[#27c86f]/30 bg-[#27c86f]/10 p-3">
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                Top Achievements
              </p>
              <ul className="mt-2 space-y-1 text-sm">
                {(healthScore.strengths.length > 0
                  ? healthScore.strengths
                  : ["Consistent report generation and deterministic coverage."]
                )
                  .slice(0, 3)
                  .map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
              </ul>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[#ff6a82]/30 bg-[#ff6a82]/10 p-3">
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                Major Concerns
              </p>
              <ul className="mt-2 space-y-1 text-sm">
                {(topRisks.length > 0
                  ? topRisks.map((item) => item.label)
                  : ["No high-severity risks were detected in this period."]
                )
                  .slice(0, 3)
                  .map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
              </ul>
            </div>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Financial Health"
        description="Reused health scoring components with strengths, weaknesses, and actions."
        className="break-inside-avoid"
      >
        {healthAIUnavailable ? (
          <AIUnavailableCard onRetry={() => void healthQuery.refetch()} />
        ) : null}

        <div
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
          aria-label="Financial health metric grid"
        >
          {metrics.map((metric, index) => (
            <HealthMetricCard
              key={metric.key}
              title={metric.title}
              score={metric.score}
              description={HEALTH_METRIC_DESCRIPTIONS[metric.key]}
              index={index}
            />
          ))}
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <div className="space-y-3" aria-label="Financial health strengths">
            {(healthScore.strengths.length > 0
              ? healthScore.strengths
              : ["No strengths were provided for this statement."]
            )
              .slice(0, 4)
              .map((item) => (
                <StrengthCard key={item} text={item} />
              ))}
          </div>
          <div className="space-y-3" aria-label="Financial health weaknesses">
            {(healthScore.weaknesses.length > 0
              ? healthScore.weaknesses
              : ["No weaknesses were provided for this statement."]
            )
              .slice(0, 4)
              .map((item) => (
                <WeaknessCard key={item} text={item} />
              ))}
          </div>
        </div>

        <div
          className="grid gap-3"
          aria-label="Financial health recommendations"
        >
          {(healthScore.recommendations.length > 0
            ? healthScore.recommendations
            : [
                "Continue maintaining spending discipline and monitor trends weekly.",
              ]
          )
            .slice(0, 3)
            .map((recommendation, index) => (
              <HealthRecommendationCard
                key={recommendation}
                recommendation={recommendation}
                priority={index === 0 ? "high" : index === 1 ? "medium" : "low"}
              />
            ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Income Overview"
        description="Income performance, stability, and primary contributing sources."
        className="break-inside-avoid"
      >
        <div
          className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
          aria-label="Income overview cards"
        >
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Total Income
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(totalIncome, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Average Income
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(incomeTotals.averageIncome, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Largest Income Source
            </p>
            <p className="mt-2 text-sm font-semibold">
              {incomeTotals.largestIncomeLabel || "N/A"}
            </p>
            <p className="text-sm text-[var(--text-muted)]">
              {formatCurrency(incomeTotals.largestIncome, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Income Stability
            </p>
            <p className="mt-2 text-xl font-semibold">
              {incomeTotals.stabilityScore.toFixed(0)}/100
            </p>
          </div>
        </div>

        <div
          className="grid gap-4 xl:grid-cols-2"
          aria-label="Income overview charts"
        >
          <CategoryChart
            categoryData={incomeTotals.sources.map((item) => ({
              name: item.label,
              value: item.amount,
            }))}
            paymentChannelData={[
              { name: "Income", value: Math.max(totalIncome, 0) },
              { name: "Net", value: Math.max(netCashFlow, 0) },
            ]}
          />
          <CashFlowChart monthlyTrend={trendPoints} />
        </div>
      </SectionCard>

      <SectionCard
        title="Expense Overview"
        description="Category distribution, merchants, largest expenses, and payment mix."
        className="break-inside-avoid"
      >
        <div
          className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
          aria-label="Expense overview cards"
        >
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Total Expenses
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(totalExpenses, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Largest Expense
            </p>
            <p className="mt-2 text-sm font-semibold">
              {expenseBreakdown.largestExpenseLabel || "N/A"}
            </p>
            <p className="text-sm text-[var(--text-muted)]">
              {formatCurrency(expenseBreakdown.largestExpense, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Top Merchant
            </p>
            <p className="mt-2 text-sm font-semibold">
              {expenseBreakdown.merchants[0]?.merchant ?? "N/A"}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Monthly Spending
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(totalExpenses, currencyCode)}
            </p>
          </div>
        </div>

        <div
          className="grid gap-4 xl:grid-cols-2"
          aria-label="Expense overview charts"
        >
          <CategoryChart
            categoryData={expenseBreakdown.categoryDistribution}
            paymentChannelData={expenseBreakdown.paymentChannels}
          />
          <MerchantChart merchants={expenseBreakdown.merchants.slice(0, 8)} />
        </div>
      </SectionCard>

      <SectionCard
        title="Cash Flow"
        description="Income, expenses, net trajectory, and monthly trend comparison."
        className="break-inside-avoid"
      >
        <div
          className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
          aria-label="Cash flow cards"
        >
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Income
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(totalIncome, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Expenses
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(totalExpenses, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Net Cash Flow
            </p>
            <p className="mt-2 text-xl font-semibold">
              {formatCurrency(netCashFlow, currencyCode)}
            </p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Savings Rate
            </p>
            <p className="mt-2 text-xl font-semibold">
              {savingsRate.toFixed(1)}%
            </p>
          </div>
        </div>

        <CashFlowChart monthlyTrend={trendPoints} />
      </SectionCard>

      <SectionCard
        title="Budget Recommendations"
        description="Reused budget comparison, charting, and top savings opportunities."
        className="break-inside-avoid"
      >
        {budgetAIUnavailable ? (
          <AIUnavailableCard onRetry={() => void budgetQuery.refetch()} />
        ) : null}

        {budgetQuery.data ? (
          <>
            <BudgetComparisonTable
              rows={budgetRows}
              currencyFormatter={(value) => formatCurrency(value, currencyCode)}
            />
            <BudgetChart data={budgetChartData} />
            <div
              className="grid gap-3"
              aria-label="Budget savings opportunities"
            >
              {budgetPrioritySort(budgetQuery.data.priority_recommendations)
                .slice(0, 3)
                .map((item) => (
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
          </>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">
            Budget recommendation details are unavailable for this statement.
          </p>
        )}
      </SectionCard>

      <SectionCard
        title="Spending Insights"
        description="Reused insight cards and charts for observations, recurring payments, and merchant highlights."
        className="break-inside-avoid"
      >
        {insightsAIUnavailable ? (
          <AIUnavailableCard onRetry={() => void insightsQuery.refetch()} />
        ) : null}

        <InsightGrid
          highSpending={formatCurrency(
            expenseBreakdown.largestExpense,
            currencyCode,
          )}
          savingsOpportunity={`${savingsRate.toFixed(1)}% Savings Rate`}
          largestMerchant={expenseBreakdown.merchants[0]?.merchant ?? "N/A"}
          largestCategory={
            expenseBreakdown.categoryDistribution[0]?.name ?? "N/A"
          }
          recurringPayments={String(
            insightsQuery.data?.deterministic_summary.recurring_subscriptions
              .length ?? asNumber(spendingSummary.recurring_payments),
          )}
          subscriptions={
            insightsQuery.data?.deterministic_summary.recurring_subscriptions[0]
              ?.merchant ?? "None detected"
          }
        />
      </SectionCard>

      <SectionCard
        title="Financial Risks"
        description="Risk indicators prioritized by potential severity and urgency."
        className="break-inside-avoid"
      >
        {topRisks.length === 0 ? (
          <div className="rounded-[var(--radius-md)] border border-[#27c86f]/30 bg-[#27c86f]/10 p-4 text-sm">
            No significant financial risks were detected in this report.
          </div>
        ) : (
          <div
            className="grid gap-3 md:grid-cols-2"
            aria-label="Financial risk cards"
          >
            {topRisks.map((risk) => (
              <div
                key={risk.label}
                className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-semibold">{risk.label}</p>
                  <Badge
                    variant="muted"
                    className={
                      risk.severity === "high"
                        ? "bg-[#ff6a82]/20 text-[#ff6a82]"
                        : risk.severity === "medium"
                          ? "bg-[#f3972e]/20 text-[#f3972e]"
                          : "bg-[#29d0b3]/20 text-[#29d0b3]"
                    }
                  >
                    {risk.severity}
                  </Badge>
                </div>
                <div className="mt-2 inline-flex items-center gap-2 text-xs text-[var(--text-muted)]">
                  {risk.severity === "high" ? (
                    <ShieldAlert className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                  ) : risk.severity === "medium" ? (
                    <AlertTriangle className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                  ) : (
                    <ShieldCheck className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                  )}
                  Risk assessment explanation included in advisor summary.
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="Action Plan"
        description="Top three prioritized actions with expected monthly impact."
        className="break-inside-avoid"
      >
        <div className="grid gap-3" aria-label="Action plan list">
          {topActions.map((action) => (
            <div
              key={action.title}
              className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold">{action.title}</p>
                <Badge variant="muted" className="uppercase">
                  {action.priority}
                </Badge>
              </div>
              <div className="mt-2 grid gap-1 text-sm text-[var(--text-muted)] sm:grid-cols-2">
                <p>Focus Area: {action.category}</p>
                <p>
                  Estimated Monthly Savings:{" "}
                  {formatCurrency(action.savings, currencyCode)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      {healthAIUnavailable ||
      insightsAIUnavailable ||
      budgetAIUnavailable ||
      reportAIUnavailable ? (
        <div
          className="rounded-[var(--radius-md)] border border-[#4f8df7]/35 bg-[#4f8df7]/10 p-4 text-sm text-[var(--text-muted)]"
          aria-label="Deterministic fallback notice"
        >
          <div className="inline-flex items-center gap-2 font-medium text-[var(--text)]">
            <Sparkles className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            AI-driven sections are temporarily degraded.
          </div>
          <p className="mt-2">
            Deterministic report sections remain available and continue to
            provide reliable financial analysis.
          </p>
        </div>
      ) : null}
    </div>
  );
}
