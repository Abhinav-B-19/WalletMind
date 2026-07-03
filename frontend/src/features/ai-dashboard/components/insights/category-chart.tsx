import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type CategoryPoint = {
  name: string;
  value: number;
};

type PaymentPoint = {
  name: string;
  value: number;
};

type CategoryChartProps = {
  categoryData: CategoryPoint[];
  paymentChannelData: PaymentPoint[];
};

const COLORS = [
  "#4f8df7",
  "#29d0b3",
  "#e3be37",
  "#ff6a82",
  "#8b5cf6",
  "#06b6d4",
];

export function CategoryChart({
  categoryData,
  paymentChannelData,
}: CategoryChartProps) {
  return (
    <SectionCard
      title="Category & Payment Mix"
      description="Category spending and payment channel breakdown."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-2" aria-label="Category spending chart">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Category Spending
          </p>
          <div className="h-64 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={categoryData}
                margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(148,163,184,0.25)"
                />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {categoryData.map((entry, index) => (
                    <Cell
                      key={`${entry.name}-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-2" aria-label="Payment channel chart">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Payment Channel Breakdown
          </p>
          <div className="h-64 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip />
                <Pie
                  data={paymentChannelData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={82}
                  label
                >
                  {paymentChannelData.map((entry, index) => (
                    <Cell
                      key={`${entry.name}-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
