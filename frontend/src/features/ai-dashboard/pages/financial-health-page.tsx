import { useMemo } from "react";
import { CalendarClock, Sparkles } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";
import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";
import {
  HealthMetricCard,
  LegendCard,
  RecommendationCard,
  StrengthCard,
  WeaknessCard,
  healthStyleForScore,
} from "@/features/ai-dashboard/components/financial-health";
import { EmptyStateCard } from "@/features/ai-dashboard/components/empty-state-card";
import { ErrorCard } from "@/features/ai-dashboard/components/error-card";
import { HealthScoreGauge } from "@/features/ai-dashboard/components/health-score-gauge";
import { LoadingCard } from "@/features/ai-dashboard/components/loading-card";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import { useHealthScore } from "@/features/ai-dashboard/hooks";
import { isAIUnavailableError } from "@/features/ai-dashboard/services/ai-degradation";

const metricDescriptions: Record<string, string> = {
  savings_rate: "How consistently you retain income after expenses.",
  income_stability: "How stable your monthly income pattern appears.",
  spending_discipline:
    "How effectively your spending aligns with healthy limits.",
  recurring_obligations:
    "How manageable recurring commitments are vs your income.",
  cash_flow: "How positive and steady your overall net cash flow is.",
};

const metricLabels: Record<string, string> = {
  savings_rate: "Savings Rate",
  income_stability: "Income Stability",
  spending_discipline: "Spending Discipline",
  recurring_obligations: "Recurring Obligations",
  cash_flow: "Cash Flow",
};

export function FinancialHealthPage() {
  const [searchParams] = useSearchParams();
  const statementUuid = searchParams.get("statement_id");

  const healthQuery = useHealthScore(statementUuid);
  const healthAIUnavailable =
    healthQuery.isError && isAIUnavailableError(healthQuery.error);
  const generatedAt = useMemo(() => {
    if (!healthQuery.data) {
      return null;
    }

    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date());
  }, [healthQuery.data]);

  const metrics = useMemo(() => {
    if (!healthQuery.data) {
      return [];
    }

    const { components } = healthQuery.data;
    return [
      {
        key: "savings_rate",
        title: metricLabels.savings_rate,
        score: components.savings_rate,
      },
      {
        key: "income_stability",
        title: metricLabels.income_stability,
        score: components.income_stability,
      },
      {
        key: "spending_discipline",
        title: metricLabels.spending_discipline,
        score: components.spending_discipline,
      },
      {
        key: "recurring_obligations",
        title: metricLabels.recurring_obligations,
        score: components.recurring_obligations,
      },
      {
        key: "cash_flow",
        title: metricLabels.cash_flow,
        score: components.cash_flow,
      },
    ];
  }, [healthQuery.data]);

  if (!statementUuid) {
    return (
      <div className="space-y-6" aria-label="Financial health page empty state">
        <PageTitle
          title="Financial Health"
          subtitle="Deep-dive into your financial health score and component breakdown."
        />
        <EmptyStateCard
          title="No Statement Selected"
          description="Open AI Dashboard and select a processed statement first, then jump into Financial Health."
          ctaLabel="Open AI Dashboard"
          ctaHref="/app/dashboard"
          ariaLabel="No statement selected"
        />
      </div>
    );
  }

  if (healthQuery.isLoading) {
    return (
      <div className="space-y-6" aria-label="Financial health page loading">
        <PageTitle
          title="Financial Health"
          subtitle="Deep-dive into your financial health score and component breakdown."
        />
        <LoadingCard ariaLabel="Loading financial health hero" lines={6} />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <LoadingCard
            ariaLabel="Loading financial health metric card"
            lines={4}
            compact
          />
          <LoadingCard
            ariaLabel="Loading financial health metric card"
            lines={4}
            compact
          />
          <LoadingCard
            ariaLabel="Loading financial health metric card"
            lines={4}
            compact
          />
        </div>
      </div>
    );
  }

  if (healthQuery.isError && !healthQuery.data) {
    return (
      <div className="space-y-6" aria-label="Financial health page error">
        <PageTitle
          title="Financial Health"
          subtitle="Deep-dive into your financial health score and component breakdown."
        />
        <ErrorCard
          title="Unable to load financial health"
          message={
            healthQuery.error instanceof Error
              ? healthQuery.error.message
              : "Please retry in a moment."
          }
          onRetry={() => void healthQuery.refetch()}
        />
      </div>
    );
  }

  if (!healthQuery.data) {
    return null;
  }

  const style = healthStyleForScore(healthQuery.data.overall_score);

  return (
    <div className="space-y-6" aria-label="Financial health page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageTitle
          title="Financial Health"
          subtitle="Deep-dive into your financial health score and component breakdown."
        />
        <Button asChild variant="secondary">
          <Link to={`/app/dashboard?statement_id=${statementUuid}`}>
            Back to AI Dashboard
          </Link>
        </Button>
      </div>

      <SectionCard
        title="Health Score Overview"
        description="Deterministic score with AI explanation and practical guidance."
        className="animate-in fade-in duration-500"
        action={
          <Badge variant="muted" className={style.badgeClassName}>
            {style.label}
          </Badge>
        }
      >
        <div className="grid gap-6 lg:grid-cols-[auto_1fr] lg:items-center">
          <div className="mx-auto lg:mx-0">
            <HealthScoreGauge
              score={healthQuery.data.overall_score}
              grade={healthQuery.data.grade}
            />
          </div>

          <div className="space-y-4">
            {healthAIUnavailable ? (
              <AIUnavailableCard onRetry={() => void healthQuery.refetch()} />
            ) : (
              <p className="text-base text-[var(--text-muted)]">
                {healthQuery.data.ai_explanation}
              </p>
            )}
            <div className="inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--text-muted)]">
              <CalendarClock className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              Last generated: {generatedAt}
            </div>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Component Breakdown"
        description="How each dimension contributes to your overall financial health."
      >
        <section
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
          aria-label="Health component grid"
        >
          {metrics.map((metric, index) => (
            <HealthMetricCard
              key={metric.key}
              title={metric.title}
              score={metric.score}
              description={metricDescriptions[metric.key]}
              index={index}
            />
          ))}
        </section>
      </SectionCard>

      <section className="grid gap-4 xl:grid-cols-2">
        <SectionCard
          title="Strengths"
          description="What you are already doing well."
        >
          <div className="grid gap-3">
            {healthQuery.data.strengths.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">
                No explicit strengths were returned for this statement.
              </p>
            ) : (
              healthQuery.data.strengths.map((strength) => (
                <StrengthCard key={strength} text={strength} />
              ))
            )}
          </div>
        </SectionCard>

        <SectionCard
          title="Weaknesses"
          description="Areas where small changes can significantly improve your score."
        >
          <div className="grid gap-3">
            {healthQuery.data.weaknesses.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">
                No weaknesses were returned for this statement.
              </p>
            ) : (
              healthQuery.data.weaknesses.map((weakness) => (
                <WeaknessCard key={weakness} text={weakness} />
              ))
            )}
          </div>
        </SectionCard>
      </section>

      <SectionCard
        title="Recommendations"
        description="AI-guided actions to improve your financial health over time."
      >
        {healthAIUnavailable ? (
          <AIUnavailableCard onRetry={() => void healthQuery.refetch()} />
        ) : (
          <div className="grid gap-3">
            {healthQuery.data.recommendations.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">
                No recommendations are currently available.
              </p>
            ) : (
              healthQuery.data.recommendations.map((recommendation, index) => (
                <RecommendationCard
                  key={recommendation}
                  recommendation={recommendation}
                  priority={
                    index === 0 ? "high" : index === 1 ? "medium" : "low"
                  }
                />
              ))
            )}
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="Health Legend"
        description="Score ranges used to classify financial health quality."
        action={
          <span className="inline-flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Sparkles className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            Interpretation Guide
          </span>
        }
      >
        <LegendCard />
      </SectionCard>
    </div>
  );
}
