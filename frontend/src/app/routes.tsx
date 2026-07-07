import { Navigate, createRoutesFromElements, Route } from "react-router-dom";

import {
  AIFeatureRoute,
  ProtectedRoute,
  PublicOnlyRoute,
} from "@/components/auth/route-guards";
import { AppLayout } from "@/components/layout/app-layout";
import { PublicLayout } from "@/components/layout/public-layout";
import { AppChatPage } from "@/pages/app-chat-page";
import { AppBudgetRecommendationsPage } from "@/pages/app-budget-recommendations-page";
import { AppDashboardPage } from "@/pages/app-dashboard-page";
import { AppFinancialHealthPage } from "@/pages/app-financial-health-page";
import { AppAgentPlaygroundPage } from "@/pages/app-agent-playground-page";
import { AppInsightsPage } from "@/pages/app-insights-page";
import { AppPlannerPage } from "@/pages/app-planner-page";
import { AppSettingsPage } from "@/pages/app-settings-page";
import { AppStatementUploadPage } from "@/pages/app-statement-upload-page";
import { AppStatementsPage } from "@/pages/app-statements-page";
import { HomePage } from "@/pages/landing-page";
import { JudgeHubPage } from "@/pages/judge-hub-page";
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
      <Route index element={<Navigate to="judge" replace />} />
      <Route path="judge" element={<JudgeHubPage />} />
      <Route path="home" element={<WorkspacePage />} />
      <Route
        path="agent-playground"
        element={
          <AIFeatureRoute>
            <AppAgentPlaygroundPage />
          </AIFeatureRoute>
        }
      />
      <Route path="statements" element={<AppStatementsPage />} />
      <Route path="statements/upload" element={<AppStatementUploadPage />} />
      <Route
        path="dashboard"
        element={
          <AIFeatureRoute>
            <AppDashboardPage />
          </AIFeatureRoute>
        }
      />
      <Route
        path="budget"
        element={
          <AIFeatureRoute>
            <AppBudgetRecommendationsPage />
          </AIFeatureRoute>
        }
      />
      <Route
        path="insights"
        element={
          <AIFeatureRoute>
            <AppInsightsPage />
          </AIFeatureRoute>
        }
      />
      <Route
        path="health"
        element={
          <AIFeatureRoute>
            <AppFinancialHealthPage />
          </AIFeatureRoute>
        }
      />
      <Route
        path="planner"
        element={
          <AIFeatureRoute>
            <AppPlannerPage />
          </AIFeatureRoute>
        }
      />
      <Route
        path="chat"
        element={
          <AIFeatureRoute>
            <AppChatPage />
          </AIFeatureRoute>
        }
      />
      <Route path="settings" element={<AppSettingsPage />} />
    </Route>

    <Route
      path="/agent-playground"
      element={<Navigate to="/app/agent-playground" replace />}
    />

    <Route path="/judge" element={<Navigate to="/app/judge" replace />} />

    <Route path="*" element={<NotFoundPage />} />
  </>,
);
