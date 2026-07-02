import type { PropsWithChildren } from "react";

export function ContentContainer({ children }: PropsWithChildren) {
  return (
    <div className="mx-auto w-full max-w-[1200px] px-4 py-6 md:px-6 md:py-8">
      {children}
    </div>
  );
}
