import {
  BadgeDollarSign,
  CalendarSync,
  CreditCard,
  Landmark,
  ReceiptText,
  Store,
} from "lucide-react";

import { InsightCard } from "@/features/ai-dashboard/components/insights/insight-card";

type InsightGridProps = {
  highSpending: string;
  savingsOpportunity: string;
  largestMerchant: string;
  largestCategory: string;
  recurringPayments: string;
  subscriptions: string;
};

export function InsightGrid({
  highSpending,
  savingsOpportunity,
  largestMerchant,
  largestCategory,
  recurringPayments,
  subscriptions,
}: InsightGridProps) {
  return (
    <section
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
      aria-label="Insight key metrics"
    >
      <InsightCard
        title="High Spending"
        value={highSpending}
        description="Largest expense captured in this statement."
        icon={BadgeDollarSign}
      />
      <InsightCard
        title="Savings Opportunity"
        value={savingsOpportunity}
        description="Potential optimization from AI and deterministic signals."
        icon={Landmark}
      />
      <InsightCard
        title="Largest Merchant"
        value={largestMerchant}
        description="Merchant with the highest accumulated outflow."
        icon={Store}
      />
      <InsightCard
        title="Largest Category"
        value={largestCategory}
        description="Category currently driving the highest spending share."
        icon={ReceiptText}
      />
      <InsightCard
        title="Recurring Payments"
        value={recurringPayments}
        description="Detected recurring subscription or payment entries."
        icon={CalendarSync}
      />
      <InsightCard
        title="Subscriptions"
        value={subscriptions}
        description="Top recurring merchant and total subscription load."
        icon={CreditCard}
      />
    </section>
  );
}
