import { LoadingCard } from "@/features/ai-dashboard/components/loading-card";

export function LoadingSkeleton() {
  return (
    <div className="space-y-4" aria-label="Budget page loading state">
      <LoadingCard ariaLabel="Loading budget hero" lines={5} />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <LoadingCard
            key={`budget-overview-${index}`}
            ariaLabel="Loading budget overview card"
            lines={3}
            compact
          />
        ))}
      </div>
      <LoadingCard ariaLabel="Loading budget table" lines={7} />
      <div className="grid gap-4 xl:grid-cols-2">
        <LoadingCard ariaLabel="Loading budget chart" lines={6} />
        <LoadingCard ariaLabel="Loading budget chart" lines={6} />
      </div>
    </div>
  );
}
