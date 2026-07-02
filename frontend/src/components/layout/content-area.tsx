import type { PropsWithChildren } from "react";

export function ContentArea({ children }: PropsWithChildren) {
  return (
    <main className="min-w-0 flex-1 border-l border-[var(--border)]/70">
      <div className="mx-auto w-full max-w-[1200px] px-4 py-6 md:px-8 md:py-8">
        {children}
      </div>
    </main>
  );
}
