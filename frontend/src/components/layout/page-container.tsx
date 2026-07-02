import type { PropsWithChildren } from "react";

export function PageContainer({ children }: PropsWithChildren) {
  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col md:flex-row">
      {children}
    </div>
  );
}
