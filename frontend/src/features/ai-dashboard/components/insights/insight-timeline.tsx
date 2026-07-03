import { CalendarDays } from "lucide-react";

import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type TimelineItem = {
  month: string;
  note: string;
};

type InsightTimelineProps = {
  items: TimelineItem[];
};

export function InsightTimeline({ items }: InsightTimelineProps) {
  return (
    <SectionCard
      title="Insights Timeline"
      description="Chronological financial observations extracted from monthly trend behavior."
    >
      <ol className="space-y-3" aria-label="Insights timeline">
        {items.length === 0 ? (
          <li className="text-sm text-[var(--text-muted)]">
            No timeline observations are available for the selected statement.
          </li>
        ) : (
          items.map((item) => (
            <li
              key={`${item.month}-${item.note}`}
              className="flex gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3"
            >
              <div className="mt-0.5 text-[var(--primary)]">
                <CalendarDays className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              </div>
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                  {item.month}
                </p>
                <p className="text-sm text-[var(--text)]">{item.note}</p>
              </div>
            </li>
          ))
        )}
      </ol>
    </SectionCard>
  );
}
