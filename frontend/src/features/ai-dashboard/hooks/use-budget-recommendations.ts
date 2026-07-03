import { useQuery } from "@tanstack/react-query";

import { getBudgetRecommendations } from "@/features/ai-dashboard/services/ai-dashboard-api";

export function useBudgetRecommendations(statementUuid: string | null) {
  return useQuery({
    queryKey: ["ai-dashboard", "budget-recommendations", statementUuid],
    queryFn: () => getBudgetRecommendations(statementUuid ?? ""),
    enabled: Boolean(statementUuid),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
    retry: 1,
  });
}
