import { useEffect } from "react";
import { Outlet } from "react-router-dom";

import { ContentArea } from "@/components/layout/content-area";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TopHeader } from "@/components/layout/top-header";
import { getGeminiKeyStatus } from "@/lib/api/ai-key";
import { clearAIKeyStatus, setAIKeyStatus } from "@/lib/auth/ai-key-storage";

export function AppLayout() {
  useEffect(() => {
    let active = true;

    const syncStatus = async () => {
      try {
        const status = await getGeminiKeyStatus();
        if (!active) {
          return;
        }
        setAIKeyStatus(status.configured, status.source);
      } catch {
        if (!active) {
          return;
        }
        clearAIKeyStatus();
      }
    };

    void syncStatus();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="h-screen overflow-hidden bg-[var(--bg)] text-[var(--text)]">
      <TopHeader />
      <PageContainer>
        <Sidebar />
        <ContentArea>
          <Outlet />
        </ContentArea>
      </PageContainer>
    </div>
  );
}
