import { LoaderCircle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type LoadingStateProps = {
  title?: string;
};

export function LoadingState({ title = "Loading..." }: LoadingStateProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-5 text-sm text-[var(--text-muted)]">
        <LoaderCircle className="h-[var(--icon-md)] w-[var(--icon-md)] animate-spin" />
        {title}
      </CardContent>
    </Card>
  );
}
