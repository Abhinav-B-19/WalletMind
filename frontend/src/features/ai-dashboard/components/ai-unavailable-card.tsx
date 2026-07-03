import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  AI_DEGRADATION_DESCRIPTION,
  AI_DEGRADATION_TITLE,
} from "@/features/ai-dashboard/services/ai-degradation";

type AIUnavailableCardProps = {
  title?: string;
  description?: string;
  onRetry: () => void;
};

export function AIUnavailableCard({
  title = AI_DEGRADATION_TITLE,
  description = AI_DEGRADATION_DESCRIPTION,
  onRetry,
}: AIUnavailableCardProps) {
  return (
    <Card
      className="border-[#4f8df7]/35 bg-[#4f8df7]/10"
      aria-label="AI unavailable card"
    >
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-[#4f8df7]/20 text-[#4f8df7]">
            <Sparkles className="h-[var(--icon-md)] w-[var(--icon-md)]" />
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-semibold">{title}</h3>
            <p className="text-sm text-[var(--text-muted)]">{description}</p>
          </div>
        </div>

        <p className="text-xs text-[var(--text-muted)]">
          Continue using deterministic features.
        </p>

        <Button type="button" variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      </CardContent>
    </Card>
  );
}
