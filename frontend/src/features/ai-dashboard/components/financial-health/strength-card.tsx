import { CheckCircle2 } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type StrengthCardProps = {
  text: string;
};

export function StrengthCard({ text }: StrengthCardProps) {
  return (
    <Card className="border-[#27c86f]/30 bg-[#27c86f]/8">
      <CardContent className="flex items-start gap-3 p-4">
        <CheckCircle2 className="mt-0.5 h-[var(--icon-md)] w-[var(--icon-md)] text-[#27c86f]" />
        <p className="text-sm">{text}</p>
      </CardContent>
    </Card>
  );
}
