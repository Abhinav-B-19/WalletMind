import { useQuery } from "@tanstack/react-query";

import { getAIServiceHealth } from "@/features/ai-dashboard/services/ai-dashboard-api";

export function useAIHealth() {
  return useQuery({
    queryKey: ["ai-dashboard", "ai-health"],
    queryFn: getAIServiceHealth,
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 10,
    retry: 1,
  });
}
