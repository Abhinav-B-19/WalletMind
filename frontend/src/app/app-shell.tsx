import { Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { LoadingScreen } from "@/components/app/loading-screen";
import { appRoutes } from "@/app/routes";

const router = createBrowserRouter(appRoutes);

export function AppShell() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <RouterProvider router={router} />
    </Suspense>
  );
}
