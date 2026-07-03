import type { UploadedStatement } from "@/lib/api/statements";

export type DashboardStatement = UploadedStatement;

export type PriorityLevel = "low" | "medium" | "high";

export type HealthComponents = {
  savings_rate: number;
  income_stability: number;
  spending_discipline: number;
  recurring_obligations: number;
  cash_flow: number;
};

export type FinancialHealthScore = {
  overall_score: number;
  grade: string;
  components: HealthComponents;
  strengths: string[];
  weaknesses: string[];
  ai_explanation: string;
  recommendations: string[];
};

export type InsightRecommendation = {
  title: string;
  description: string;
  priority: PriorityLevel;
};

export type SpendingInsights = {
  statement_uuid: string;
  deterministic_summary: Record<string, unknown>;
  insights: {
    summary: string;
    strengths: string[];
    concerns: string[];
    recommendations: InsightRecommendation[];
  };
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  finish_reason: string;
};

export type BudgetRecommendation = {
  title: string;
  priority: PriorityLevel;
  category: string;
  estimated_monthly_saving: number;
};

export type BudgetRecommendations = {
  monthly_budget: Record<
    string,
    {
      historical: number;
      recommended: number;
      potential_saving: number;
    }
  >;
  overall_potential_savings: number;
  priority_recommendations: BudgetRecommendation[];
  ai_summary: string;
  ai_recommendations: string[];
};

export type MonthlyFinancialReport = {
  executive_summary: string;
  financial_health: Record<string, unknown>;
  income_summary: Record<string, unknown>;
  expense_summary: Record<string, unknown>;
  cash_flow: {
    net_cash_flow?: number;
    savings_rate?: number;
    monthly_averages?: {
      income?: number;
      expenses?: number;
      net?: number;
    };
    monthly_trend?: Array<Record<string, unknown>>;
  };
  spending_insights: Record<string, unknown>;
  budget_recommendations: Record<string, unknown>;
  health_score: {
    overall_score?: number;
    grade?: string;
    components?: Record<string, number>;
  };
  strengths: string[];
  risks: string[];
  action_plan: string[];
};

export type AIServiceHealth = {
  configured: boolean;
  model: string;
  status: string;
};

export type HealthTone = "excellent" | "good" | "warning" | "critical";
