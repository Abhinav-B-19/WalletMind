import { z } from "zod";

import { ApiClientError, apiClient } from "@/lib/api/client";
import { listStatements, type UploadedStatement } from "@/lib/api/statements";
import type {
  AIServiceHealth,
  BudgetRecommendations,
  FinancialHealthScore,
  MonthlyFinancialReport,
  SpendingInsights,
} from "@/features/ai-dashboard/types";

const numberLikeSchema = z
  .union([z.number(), z.string()])
  .transform((value) => {
    const parsed = typeof value === "number" ? value : Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  });

const prioritySchema = z.enum(["low", "medium", "high"]);

const apiEnvelopeSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    message: z.string(),
    data: dataSchema,
  });

const healthScoreSchema = z.object({
  overall_score: z.number().int().min(0).max(100),
  grade: z.string().min(1),
  components: z.object({
    savings_rate: z.number().int().min(0).max(100),
    income_stability: z.number().int().min(0).max(100),
    spending_discipline: z.number().int().min(0).max(100),
    recurring_obligations: z.number().int().min(0).max(100),
    cash_flow: z.number().int().min(0).max(100),
  }),
  strengths: z.array(z.string()).default([]),
  weaknesses: z.array(z.string()).default([]),
  ai_explanation: z.string().min(1),
  recommendations: z.array(z.string()).default([]),
});

const insightsSchema = z.object({
  statement_uuid: z.string().uuid(),
  deterministic_summary: z.object({
    statement_uuid: z.string().uuid(),
    transaction_count: z.number().int().nonnegative(),
    credit_count: z.number().int().nonnegative(),
    debit_count: z.number().int().nonnegative(),
    cash_flow: z.object({
      total_income: numberLikeSchema,
      total_expenses: numberLikeSchema,
      net_cash_flow: numberLikeSchema,
      savings_rate: numberLikeSchema,
    }),
    category_breakdown: z.record(z.string(), numberLikeSchema),
    top_spending_categories: z
      .array(
        z.object({
          category: z.string().min(1),
          amount: numberLikeSchema,
        }),
      )
      .default([]),
    top_merchants: z
      .array(
        z.object({
          merchant: z.string().min(1),
          amount: numberLikeSchema,
        }),
      )
      .default([]),
    largest_expense: z
      .object({
        date: z.string().min(1),
        amount: numberLikeSchema,
        category: z.string().nullable(),
        merchant: z.string().min(1),
      })
      .nullable(),
    largest_income: z
      .object({
        date: z.string().min(1),
        amount: numberLikeSchema,
        category: z.string().nullable(),
        merchant: z.string().min(1),
      })
      .nullable(),
    monthly_averages: z.object({
      income: numberLikeSchema,
      expenses: numberLikeSchema,
      net: numberLikeSchema,
    }),
    monthly_trend: z
      .array(
        z.object({
          month: z.string().min(1),
          income: numberLikeSchema,
          expenses: numberLikeSchema,
          net: numberLikeSchema,
        }),
      )
      .default([]),
    recurring_subscriptions: z
      .array(
        z.object({
          merchant: z.string().min(1),
          amount: numberLikeSchema,
        }),
      )
      .default([]),
  }),
  insights: z.object({
    summary: z.string().min(1),
    strengths: z.array(z.string()).default([]),
    concerns: z.array(z.string()).default([]),
    recommendations: z
      .array(
        z.object({
          title: z.string().min(1),
          description: z.string().min(1),
          priority: prioritySchema,
        }),
      )
      .default([]),
  }),
  model: z.string().min(1),
  prompt_tokens: z.number().int().nonnegative(),
  completion_tokens: z.number().int().nonnegative(),
  total_tokens: z.number().int().nonnegative(),
  finish_reason: z.string().min(1),
});

const budgetRecommendationsSchema = z.object({
  monthly_budget: z.record(
    z.string(),
    z.object({
      historical: numberLikeSchema,
      recommended: numberLikeSchema,
      potential_saving: numberLikeSchema,
    }),
  ),
  overall_potential_savings: numberLikeSchema,
  priority_recommendations: z
    .array(
      z.object({
        title: z.string().min(1),
        priority: prioritySchema,
        category: z.string().min(1),
        estimated_monthly_saving: numberLikeSchema,
      }),
    )
    .default([]),
  ai_summary: z.string().min(1),
  ai_recommendations: z.array(z.string()).default([]),
});

const monthlyReportSchema = z.object({
  executive_summary: z.string().min(1),
  financial_health: z.record(z.string(), z.unknown()),
  income_summary: z.record(z.string(), z.unknown()),
  expense_summary: z.record(z.string(), z.unknown()),
  cash_flow: z
    .object({
      net_cash_flow: numberLikeSchema.optional(),
      savings_rate: numberLikeSchema.optional(),
      monthly_averages: z
        .object({
          income: numberLikeSchema.optional(),
          expenses: numberLikeSchema.optional(),
          net: numberLikeSchema.optional(),
        })
        .optional(),
      monthly_trend: z.array(z.record(z.string(), z.unknown())).optional(),
    })
    .passthrough(),
  spending_insights: z.record(z.string(), z.unknown()),
  budget_recommendations: z.record(z.string(), z.unknown()),
  health_score: z
    .object({
      overall_score: numberLikeSchema.optional(),
      grade: z.string().optional(),
      components: z.record(z.string(), numberLikeSchema).optional(),
    })
    .passthrough(),
  strengths: z.array(z.string()).default([]),
  risks: z.array(z.string()).default([]),
  action_plan: z.array(z.string()).default([]),
});

const aiHealthSchema = z.object({
  configured: z.boolean(),
  model: z.string().min(1),
  status: z.string().min(1),
});

function toApiError(error: unknown, fallbackMessage: string): Error {
  if (error instanceof z.ZodError) {
    return new Error("Unexpected dashboard response format from backend.");
  }

  if (error instanceof ApiClientError) {
    return error;
  }

  if (error instanceof Error) {
    return new Error(error.message || fallbackMessage);
  }

  return new Error(fallbackMessage);
}

export async function listProcessedStatements(
  userUuid: string,
): Promise<UploadedStatement[]> {
  const statements = await listStatements(userUuid);
  return statements
    .filter(
      (statement) =>
        statement.parsed_transaction_count > 0 || Boolean(statement.parsed_at),
    )
    .sort(
      (left, right) =>
        new Date(right.uploaded_at).getTime() -
        new Date(left.uploaded_at).getTime(),
    );
}

export async function getAIServiceHealth(): Promise<AIServiceHealth> {
  try {
    const response = await apiClient.get("/ai/health");
    return apiEnvelopeSchema(aiHealthSchema).parse(response.data).data;
  } catch (error) {
    throw toApiError(error, "Unable to fetch AI service health.");
  }
}

export async function getHealthScore(
  statementUuid: string,
): Promise<FinancialHealthScore> {
  try {
    const response = await apiClient.get(
      `/statements/${statementUuid}/health-score`,
    );
    return apiEnvelopeSchema(healthScoreSchema).parse(response.data).data;
  } catch (error) {
    throw toApiError(error, "Unable to load health score right now.");
  }
}

export async function getInsights(
  statementUuid: string,
): Promise<SpendingInsights> {
  try {
    const response = await apiClient.get(
      `/statements/${statementUuid}/insights`,
    );
    return apiEnvelopeSchema(insightsSchema).parse(response.data).data;
  } catch (error) {
    throw toApiError(error, "Unable to load AI insights right now.");
  }
}

export async function getBudgetRecommendations(
  statementUuid: string,
): Promise<BudgetRecommendations> {
  try {
    const response = await apiClient.get(
      `/statements/${statementUuid}/budget-recommendations`,
    );
    return apiEnvelopeSchema(budgetRecommendationsSchema).parse(response.data)
      .data;
  } catch (error) {
    throw toApiError(error, "Unable to load budget recommendations right now.");
  }
}

export async function getMonthlyReport(
  statementUuid: string,
): Promise<MonthlyFinancialReport> {
  try {
    const response = await apiClient.get(
      `/statements/${statementUuid}/monthly-report`,
    );
    return apiEnvelopeSchema(monthlyReportSchema).parse(response.data).data;
  } catch (error) {
    throw toApiError(error, "Unable to load monthly report right now.");
  }
}
