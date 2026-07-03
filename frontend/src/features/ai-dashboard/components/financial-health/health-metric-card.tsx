import { useEffect, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { healthStyleForScore } from "@/features/ai-dashboard/components/financial-health/health-visuals";

type HealthMetricCardProps = {
  title: string;
  score: number;
  description: string;
  index: number;
};

export function HealthMetricCard({
  title,
  score,
  description,
  index,
}: HealthMetricCardProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const style = healthStyleForScore(clamped);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(
      () => {
        setProgress(clamped);
      },
      80 + index * 80,
    );

    return () => window.clearTimeout(timer);
  }, [clamped, index]);

  return (
    <Card
      className="animate-in fade-in duration-500"
      style={{ animationDelay: `${index * 90}ms` }}
      aria-label={`${title} score card`}
    >
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">{title}</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              {description}
            </p>
          </div>
          <p className={`text-xl font-bold ${style.textClassName}`}>
            {clamped}
          </p>
        </div>

        <div
          className="h-2 rounded-full bg-[var(--surface-soft)]"
          aria-label={`${title} progress`}
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={clamped}
        >
          <div
            className="h-2 rounded-full transition-[width] duration-700 ease-out"
            style={{
              width: `${progress}%`,
              backgroundColor: style.color,
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
