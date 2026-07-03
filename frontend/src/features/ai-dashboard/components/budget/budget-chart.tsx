import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type CategoryChartPoint = {
  category: string;
  current: number;
  recommended: number;
  savings: number;
  runningSavings: number;
};

type BudgetChartProps = {
  data: CategoryChartPoint[];
};

export function BudgetChart({ data }: BudgetChartProps) {
  return (
    <section className="grid gap-4 xl:grid-cols-2" aria-label="Budget charts">
      <SectionCard
        title="Budget vs Actual"
        description="Compare current spend against recommended budget by category."
      >
        <div
          className="h-72 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2"
          aria-label="Budget versus actual chart"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.25)"
              />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="current" fill="#ff6a82" radius={[8, 8, 0, 0]} />
              <Bar dataKey="recommended" fill="#4f8df7" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      <SectionCard
        title="Savings Breakdown"
        description="Potential savings captured per category from recommended budgeting."
      >
        <div
          className="h-72 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2"
          aria-label="Savings breakdown chart"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.25)"
              />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="savings" fill="#27c86f" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      <SectionCard
        title="Category Comparison"
        description="Per-category variance between current spending and recommended levels."
      >
        <div
          className="h-72 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2"
          aria-label="Category comparison chart"
        >
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.25)"
              />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="current" fill="#ff6a82" radius={[8, 8, 0, 0]} />
              <Bar dataKey="recommended" fill="#4f8df7" radius={[8, 8, 0, 0]} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      <SectionCard
        title="Potential Savings Waterfall"
        description="Cumulative monthly savings projection from top category optimizations."
      >
        <div
          className="h-72 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2"
          aria-label="Potential savings waterfall chart"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.25)"
              />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar
                dataKey="runningSavings"
                fill="#29d0b3"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>
    </section>
  );
}
