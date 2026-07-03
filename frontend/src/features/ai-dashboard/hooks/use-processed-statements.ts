import { useQuery } from "@tanstack/react-query";

import { listProcessedStatements } from "@/features/ai-dashboard/services/ai-dashboard-api";

export function useProcessedStatements(userUuid: string | undefined) {
  return useQuery({
    queryKey: ["ai-dashboard", "processed-statements", userUuid],
    queryFn: () => listProcessedStatements(userUuid ?? ""),
    enabled: Boolean(userUuid),
    staleTime: 1000 * 30,
    gcTime: 1000 * 60 * 5,
    retry: 1,
  });
}
