import { QueryClientProvider } from "@tanstack/react-query";
import type { PropsWithChildren } from "react";

import { GlobalLoaderProvider } from "@/context/global-loader-context";
import { queryClient } from "@/lib/query-client";

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <GlobalLoaderProvider>{children}</GlobalLoaderProvider>
    </QueryClientProvider>
  );
}
