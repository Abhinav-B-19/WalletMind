import { Navigate, createRoutesFromElements, Route } from "react-router-dom";

import {
  ProtectedRoute,
  PublicOnlyRoute,
} from "@/components/auth/route-guards";
import { AppLayout } from "@/components/layout/app-layout";
import { PublicLayout } from "@/components/layout/public-layout";
import { AppChatPage } from "@/pages/app-chat-page";
import { AppDashboardPage } from "@/pages/app-dashboard-page";
import { AppPlannerPage } from "@/pages/app-planner-page";
import { AppSettingsPage } from "@/pages/app-settings-page";
import { AppStatementsPage } from "@/pages/app-statements-page";
import { HomePage } from "@/pages/landing-page";
import { LoginPage } from "@/pages/login-page";
import { NotFoundPage } from "@/pages/not-found-page";
import { RegistrationPage } from "@/pages/registration-page";
import { WorkspacePage } from "@/pages/workspace-page";

export const appRoutes = createRoutesFromElements(
  <>
    <Route element={<PublicLayout />}>
      <Route
        path="/"
        element={
          <PublicOnlyRoute>
            <HomePage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <RegistrationPage />
          </PublicOnlyRoute>
        }
      />
    </Route>

    <Route
      path="/app"
      element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Navigate to="home" replace />} />
      <Route path="home" element={<WorkspacePage />} />
      <Route path="statements" element={<AppStatementsPage />} />
      <Route path="dashboard" element={<AppDashboardPage />} />
      <Route path="planner" element={<AppPlannerPage />} />
      <Route path="chat" element={<AppChatPage />} />
      <Route path="settings" element={<AppSettingsPage />} />
    </Route>

    <Route path="*" element={<NotFoundPage />} />
  </>,
);
