import {
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
} from "recharts";
import { useEffect, useRef, useState } from "react";

import { healthBandForScore } from "@/features/ai-dashboard/components/financial-health/health-visuals";
import type { HealthTone } from "@/features/ai-dashboard/types";

const toneMap: Record<
  HealthTone,
  { stroke: string; soft: string; label: string }
> = {
  excellent: {
    stroke: "#27c86f",
    soft: "rgba(39, 200, 111, 0.16)",
    label: "Excellent",
  },
  good: {
    stroke: "#4f8df7",
    soft: "rgba(79, 141, 247, 0.16)",
    label: "Good",
  },
  fair: {
    stroke: "#e3be37",
    soft: "rgba(227, 190, 55, 0.16)",
    label: "Fair",
  },
  "needs-improvement": {
    stroke: "#f3972e",
    soft: "rgba(243, 151, 46, 0.16)",
    label: "Needs Improvement",
  },
  critical: {
    stroke: "#ff6a82",
    soft: "rgba(255, 106, 130, 0.16)",
    label: "Critical",
  },
};

export function healthToneForScore(score: number): HealthTone {
  return healthBandForScore(score);
}

type HealthScoreGaugeProps = {
  score: number;
  grade: string;
};

export function HealthScoreGauge({ score, grade }: HealthScoreGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const [displayScore, setDisplayScore] = useState(0);
  const frame = useRef<number | null>(null);
  const tone = healthToneForScore(clamped);
  const palette = toneMap[tone];

  useEffect(() => {
    const durationMs = 700;
    const startedAt = performance.now();

    const tick = (now: number) => {
      const elapsed = now - startedAt;
      const progress = Math.min(elapsed / durationMs, 1);
      setDisplayScore(Math.round(clamped * progress));

      if (progress < 1) {
        frame.current = requestAnimationFrame(tick);
      }
    };

    frame.current = requestAnimationFrame(tick);

    return () => {
      if (frame.current !== null) {
        cancelAnimationFrame(frame.current);
      }
    };
  }, [clamped]);

  return (
    <div
      className="relative h-44 w-44"
      aria-label="Financial health score gauge"
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          data={[{ value: clamped }]}
          startAngle={210}
          endAngle={-30}
          innerRadius="72%"
          outerRadius="100%"
          barSize={14}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar
            dataKey="value"
            cornerRadius={20}
            background={{ fill: "rgba(255,255,255,0.08)" }}
            fill={palette.stroke}
          />
        </RadialBarChart>
      </ResponsiveContainer>

      <div
        className="absolute inset-7 rounded-full"
        style={{
          background: `radial-gradient(circle at 30% 20%, ${palette.soft}, transparent 70%)`,
        }}
      />

      <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="text-4xl font-bold" style={{ color: palette.stroke }}>
            {displayScore}
          </p>
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Grade {grade}
          </p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {palette.label}
          </p>
        </div>
      </div>
    </div>
  );
}
