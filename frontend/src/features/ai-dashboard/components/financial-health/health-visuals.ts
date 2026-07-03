export type HealthBand =
  | "excellent"
  | "good"
  | "fair"
  | "needs-improvement"
  | "critical";

type HealthBandStyle = {
  label: string;
  color: string;
  soft: string;
  textClassName: string;
  badgeClassName: string;
};

const healthBandStyles: Record<HealthBand, HealthBandStyle> = {
  excellent: {
    label: "Excellent",
    color: "#27c86f",
    soft: "rgba(39, 200, 111, 0.16)",
    textClassName: "text-[#27c86f]",
    badgeClassName: "border-[#27c86f]/40 text-[#27c86f]",
  },
  good: {
    label: "Good",
    color: "#4f8df7",
    soft: "rgba(79, 141, 247, 0.16)",
    textClassName: "text-[#4f8df7]",
    badgeClassName: "border-[#4f8df7]/40 text-[#4f8df7]",
  },
  fair: {
    label: "Fair",
    color: "#e3be37",
    soft: "rgba(227, 190, 55, 0.16)",
    textClassName: "text-[#e3be37]",
    badgeClassName: "border-[#e3be37]/40 text-[#e3be37]",
  },
  "needs-improvement": {
    label: "Needs Improvement",
    color: "#f3972e",
    soft: "rgba(243, 151, 46, 0.16)",
    textClassName: "text-[#f3972e]",
    badgeClassName: "border-[#f3972e]/40 text-[#f3972e]",
  },
  critical: {
    label: "Critical",
    color: "#ff6a82",
    soft: "rgba(255, 106, 130, 0.16)",
    textClassName: "text-[#ff6a82]",
    badgeClassName: "border-[#ff6a82]/40 text-[#ff6a82]",
  },
};

export function healthBandForScore(score: number): HealthBand {
  if (score >= 90) {
    return "excellent";
  }
  if (score >= 75) {
    return "good";
  }
  if (score >= 60) {
    return "fair";
  }
  if (score >= 40) {
    return "needs-improvement";
  }
  return "critical";
}

export function healthStyleForScore(score: number): HealthBandStyle {
  return healthBandStyles[healthBandForScore(score)];
}

export function healthLegendItems() {
  return [
    { band: "excellent", range: "90-100" },
    { band: "good", range: "75-89" },
    { band: "fair", range: "60-74" },
    { band: "needs-improvement", range: "40-59" },
    { band: "critical", range: "Below 40" },
  ] as const;
}
