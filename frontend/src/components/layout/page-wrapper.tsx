import type { PropsWithChildren } from "react";

export function PageWrapper({ children }: PropsWithChildren) {
  return (
    <section className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)] md:p-7">
      {children}
    </section>
  );
}
