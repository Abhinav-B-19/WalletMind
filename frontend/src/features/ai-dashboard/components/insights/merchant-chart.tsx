import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type MerchantPoint = {
  merchant: string;
  amount: number;
};

type MerchantChartProps = {
  merchants: MerchantPoint[];
};

export function MerchantChart({ merchants }: MerchantChartProps) {
  return (
    <SectionCard
      title="Merchant Distribution"
      description="Top merchants by total spending in the selected statement."
    >
      <div className="space-y-2" aria-label="Merchant distribution chart">
        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
          Merchant Distribution
        </p>
        <div className="h-72 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={merchants}
              layout="vertical"
              margin={{ top: 8, right: 12, left: 20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.25)"
              />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis
                type="category"
                dataKey="merchant"
                width={120}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Bar dataKey="amount" fill="#4f8df7" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </SectionCard>
  );
}
