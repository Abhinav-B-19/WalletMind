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
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  return children;
}

export function AIFeatureRoute({ children }: PropsWithChildren) {
  const location = useLocation();

  if (!hasStoredUser()) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  return children;
}
