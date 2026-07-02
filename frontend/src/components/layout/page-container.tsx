import type { PropsWithChildren } from "react";

export function PageContainer({ children }: PropsWithChildren) {
  return (
    <div className="mx-auto flex h-[calc(100vh-73px)] w-full max-w-[1440px] flex-col overflow-hidden md:flex-row">
      {children}
    </div>
  );
}
