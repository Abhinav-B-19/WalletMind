import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type BudgetCategoryCardProps = {
  title: string;
  value: string;
  subtitle: string;
  tone: "green" | "yellow" | "red" | "neutral";
};

const toneClasses: Record<BudgetCategoryCardProps["tone"], string> = {
  green: "text-[#27c86f]",
  yellow: "text-[#e3be37]",
  red: "text-[#ff6a82]",
  neutral: "text-[#4f8df7]",
};

export function BudgetCategoryCard({
  title,
  value,
  subtitle,
  tone,
}: BudgetCategoryCardProps) {
  const TrendIcon = tone === "red" ? TrendingUp : TrendingDown;

  return (
    <Card className="border-[var(--border)] bg-[var(--surface)] shadow-sm">
      <CardContent className="space-y-2 p-4">
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            {title}
          </p>
          <TrendIcon
            className={`h-[var(--icon-sm)] w-[var(--icon-sm)] ${toneClasses[tone]}`}
          />
        </div>
        <p className="text-2xl font-semibold">{value}</p>
        <p className="text-xs text-[var(--text-muted)]">{subtitle}</p>
      </CardContent>
    </Card>
  );
}
