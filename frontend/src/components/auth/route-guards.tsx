import type { PropsWithChildren } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { isAIKeyConfigured } from "@/lib/auth/ai-key-storage";
import { hasStoredUser } from "@/lib/auth/storage";

export function PublicOnlyRoute({ children }: PropsWithChildren) {
  if (hasStoredUser()) {
    return <Navigate to="/app/judge" replace />;
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

export function AIFeatureRoute({ children }: PropsWithChildren) {
  const location = useLocation();

  if (!hasStoredUser()) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  if (!isAIKeyConfigured()) {
    return (
      <Navigate
        to="/app/home"
        replace
        state={{
          configureAIKey: true,
          from: location.pathname,
        }}
      />
    );
  }

  return children;
}
