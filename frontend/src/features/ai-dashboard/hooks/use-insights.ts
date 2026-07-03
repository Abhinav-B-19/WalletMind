import { useQuery } from "@tanstack/react-query";

import { getInsights } from "@/features/ai-dashboard/services/ai-dashboard-api";

export function useInsights(statementUuid: string | null) {
  return useQuery({
    queryKey: ["ai-dashboard", "insights", statementUuid],
    queryFn: () => getInsights(statementUuid ?? ""),
    enabled: Boolean(statementUuid),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
    retry: 1,
  });
}
