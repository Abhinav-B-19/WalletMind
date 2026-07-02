import type { PropsWithChildren } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { hasStoredUser } from "@/lib/auth/storage";

export function PublicOnlyRoute({ children }: PropsWithChildren) {
  if (hasStoredUser()) {
    return <Navigate to="/app/home" replace />;
  }

  return children;
}

export function ProtectedRoute({ children }: PropsWithChildren) {
  const location = useLocation();

  if (!hasStoredUser()) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  return children;
}
