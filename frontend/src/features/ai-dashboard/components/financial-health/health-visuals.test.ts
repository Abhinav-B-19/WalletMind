import { describe, expect, it } from "vitest";

import {
  healthBandForScore,
  healthStyleForScore,
} from "@/features/ai-dashboard/components/financial-health";

describe("health score visual mapping", () => {
  it("maps score ranges to expected bands", () => {
    expect(healthBandForScore(95)).toBe("excellent");
    expect(healthBandForScore(80)).toBe("good");
    expect(healthBandForScore(62)).toBe("fair");
    expect(healthBandForScore(48)).toBe("needs-improvement");
    expect(healthBandForScore(20)).toBe("critical");
  });

  it("returns expected colors per score", () => {
    expect(healthStyleForScore(95).color).toBe("#27c86f");
    expect(healthStyleForScore(80).color).toBe("#4f8df7");
    expect(healthStyleForScore(62).color).toBe("#e3be37");
    expect(healthStyleForScore(48).color).toBe("#f3972e");
    expect(healthStyleForScore(20).color).toBe("#ff6a82");
  });
});
