import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type CashFlowPoint = {
  month: string;
  income: number;
  expenses: number;
  net: number;
};

type CashFlowChartProps = {
  monthlyTrend: CashFlowPoint[];
};

export function CashFlowChart({ monthlyTrend }: CashFlowChartProps) {
  return (
    <SectionCard
      title="Cash Flow Trends"
      description="Monthly spending trend and income vs expense dynamics."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-2" aria-label="Monthly spending trend chart">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Monthly Spending Trend
          </p>
          <div className="h-64 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={monthlyTrend}
                margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(148,163,184,0.25)"
                />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="expenses"
                  stroke="#ff6a82"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="net"
                  stroke="#29d0b3"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-2" aria-label="Income versus expense chart">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Income vs Expense
          </p>
          <div className="h-64 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={monthlyTrend}
                margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(148,163,184,0.25)"
                />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="income" fill="#4f8df7" radius={[8, 8, 0, 0]} />
                <Bar dataKey="expenses" fill="#ff6a82" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
