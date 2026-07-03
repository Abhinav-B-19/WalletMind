import { LoadingCard } from "@/features/ai-dashboard/components/loading-card";

export function LoadingSkeleton() {
  return (
    <div className="space-y-4" aria-label="Insights page loading state">
      <LoadingCard ariaLabel="Loading insights hero" lines={5} />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <LoadingCard
            key={`insight-metric-${index}`}
            ariaLabel="Loading insight metric card"
            lines={3}
            compact
          />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <LoadingCard ariaLabel="Loading insight chart" lines={6} />
        <LoadingCard ariaLabel="Loading insight chart" lines={6} />
      </div>
      <LoadingCard ariaLabel="Loading insights timeline" lines={6} />
    </div>
  );
}
