import { useQuery } from "@tanstack/react-query";

import { getMonthlyReport } from "@/features/ai-dashboard/services/ai-dashboard-api";

export function useMonthlyReport(statementUuid: string | null) {
  return useQuery({
    queryKey: ["ai-dashboard", "monthly-report", statementUuid],
    queryFn: () => getMonthlyReport(statementUuid ?? ""),
    enabled: Boolean(statementUuid),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
    retry: 1,
  });
}
