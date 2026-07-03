import { AlertTriangle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type WeaknessCardProps = {
  text: string;
};

export function WeaknessCard({ text }: WeaknessCardProps) {
  return (
    <Card className="border-[#f3972e]/35 bg-[#f3972e]/10">
      <CardContent className="flex items-start gap-3 p-4">
        <AlertTriangle className="mt-0.5 h-[var(--icon-md)] w-[var(--icon-md)] text-[#f3972e]" />
        <p className="text-sm">{text}</p>
      </CardContent>
    </Card>
  );
}
