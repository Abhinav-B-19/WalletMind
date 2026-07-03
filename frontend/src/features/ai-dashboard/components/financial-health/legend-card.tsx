import { Card, CardContent } from "@/components/ui/card";
import {
  healthLegendItems,
  healthStyleForScore,
} from "@/features/ai-dashboard/components/financial-health/health-visuals";

export function LegendCard() {
  return (
    <Card aria-label="Health legend">
      <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
        {healthLegendItems().map((item) => {
          const scoreByBand = {
            excellent: 95,
            good: 82,
            fair: 66,
            "needs-improvement": 50,
            critical: 25,
          }[item.band];
          const style = healthStyleForScore(scoreByBand);

          return (
            <div
              key={item.band}
              className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3"
            >
              <p className={`text-sm font-semibold ${style.textClassName}`}>
                {style.label}
              </p>
              <p className="text-xs text-[var(--text-muted)]">{item.range}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
