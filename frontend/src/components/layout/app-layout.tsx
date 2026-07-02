import { Outlet } from "react-router-dom";

import { ContentArea } from "@/components/layout/content-area";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TopHeader } from "@/components/layout/top-header";

export function AppLayout() {
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
