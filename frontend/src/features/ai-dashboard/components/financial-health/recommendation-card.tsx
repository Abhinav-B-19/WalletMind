import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { healthStyleForScore } from "@/features/ai-dashboard/components/financial-health/health-visuals";

type RecommendationCardProps = {
  recommendation: string;
  priority: "high" | "medium" | "low";
};

const scoreByPriority = {
  high: 35,
  medium: 58,
  low: 72,
} as const;

export function RecommendationCard({
  recommendation,
  priority,
}: RecommendationCardProps) {
  const style = healthStyleForScore(scoreByPriority[priority]);

  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-4">
        <p className="text-sm">{recommendation}</p>
        <Badge variant="muted" className={`uppercase ${style.badgeClassName}`}>
          {priority}
        </Badge>
      </CardContent>
    </Card>
  );
}
