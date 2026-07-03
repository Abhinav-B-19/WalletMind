import { useEffect, type PropsWithChildren, type ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type DialogProps = PropsWithChildren<{
  open: boolean;
  title: string;
  description?: string;
  actions?: ReactNode;
  onClose?: () => void;
  maxWidthClassName?: string;
  contentClassName?: string;
}>;

export function Dialog({
  open,
  title,
  description,
  actions,
  children,
  onClose,
  maxWidthClassName,
  contentClassName,
}: DialogProps) {
  useEffect(() => {
    if (!open) {
      return;
    }

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  return (
    <div
      aria-hidden={!open}
      className={`fixed inset-0 z-[130] grid place-items-center px-4 transition-all duration-[var(--duration-normal)] ${
        open
          ? "pointer-events-auto opacity-100"
          : "pointer-events-none opacity-0"
      }`}
    >
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 bg-[rgba(6,10,20,0.7)] backdrop-blur-sm"
        onClick={() => onClose?.()}
      />
      <Card
        role="dialog"
        aria-modal="true"
        className={`relative z-[1] w-full ${maxWidthClassName ?? "max-w-xl"} border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-md)] transition-all duration-[var(--duration-normal)] ${
          open ? "translate-y-0 scale-100" : "translate-y-1 scale-[0.98]"
        }`}
      >
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
          {description ? (
            <p className="text-sm text-[var(--text-muted)]">{description}</p>
          ) : null}
        </CardHeader>
        <CardContent className={contentClassName ?? "space-y-4"}>
          {children}
          {actions ? (
            <div className="flex flex-wrap justify-end gap-2">{actions}</div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
