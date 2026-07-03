import { useQuery } from "@tanstack/react-query";

import { getHealthScore } from "@/features/ai-dashboard/services/ai-dashboard-api";

export function useHealthScore(statementUuid: string | null) {
  return useQuery({
    queryKey: ["ai-dashboard", "health-score", statementUuid],
    queryFn: () => getHealthScore(statementUuid ?? ""),
    enabled: Boolean(statementUuid),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
    retry: 1,
  });
}
