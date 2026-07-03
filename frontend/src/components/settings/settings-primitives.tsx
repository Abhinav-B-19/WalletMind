import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

type SettingsSectionProps = {
  title: string;
  description?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
};

type SettingsCardProps = {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

type StatusBadgeProps = {
  label: string;
  tone?: "healthy" | "warning" | "neutral" | "future";
};

type InfoRowProps = {
  label: string;
  value: ReactNode;
  className?: string;
};

type VersionCardProps = {
  title: string;
  value: string;
  meta?: string;
};

type FeatureBadgeProps = {
  feature: string;
};

type ReadOnlyFieldProps = {
  label: string;
  value: string;
  statusTone?: StatusBadgeProps["tone"];
  statusLabel?: string;
};

export function SettingsSection({
  title,
  description,
  icon,
  children,
  className,
}: SettingsSectionProps) {
  return (
    <section
      className={cn("space-y-4", className)}
      aria-label={`${title} section`}
    >
      <div className="flex items-start gap-3">
        {icon ? (
          <div className="mt-0.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2 text-[var(--primary)]">
            {icon}
          </div>
        ) : null}
        <div className="space-y-1">
          <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
          {description ? (
            <p className="text-sm text-[var(--text-muted)]">{description}</p>
          ) : null}
        </div>
      </div>
      {children}
    </section>
  );
}

export function SettingsCard({
  title,
  description,
  children,
  className,
}: SettingsCardProps) {
  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent className="space-y-2">{children}</CardContent>
    </Card>
  );
}

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  const toneClassName =
    tone === "healthy"
      ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-200"
      : tone === "warning"
        ? "border-amber-400/50 bg-amber-400/20 text-amber-100"
        : tone === "future"
          ? "border-blue-400/45 bg-blue-400/15 text-blue-100"
          : "border-[var(--border)] bg-[var(--surface-soft)] text-[var(--text-muted)]";

  return <Badge className={cn("text-xs", toneClassName)}>{label}</Badge>;
}

export function InfoRow({ label, value, className }: InfoRowProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-1 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 sm:grid-cols-[minmax(160px,1fr)_2fr] sm:items-center sm:gap-3",
        className,
      )}
    >
      <span className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
        {label}
      </span>
      <div className="font-medium text-[var(--text)]">{value}</div>
    </div>
  );
}

export function VersionCard({ title, value, meta }: VersionCardProps) {
  return (
    <Card>
      <CardContent className="space-y-2 p-5">
        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
          {title}
        </p>
        <p className="text-xl font-semibold">{value}</p>
        {meta ? (
          <p className="text-xs text-[var(--text-muted)]">{meta}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function FeatureBadge({ feature }: FeatureBadgeProps) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-sm">
      <span aria-hidden="true" className="text-emerald-300">
        ✓
      </span>
      <span className="text-emerald-100">{feature}</span>
    </div>
  );
}

export function ReadOnlyField({
  label,
  value,
  statusTone,
  statusLabel,
}: ReadOnlyFieldProps) {
  return (
    <div
      className="space-y-1 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3"
      data-testid="settings-readonly-field"
      aria-readonly="true"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
          {label}
        </p>
        {statusLabel ? (
          <StatusBadge label={statusLabel} tone={statusTone} />
        ) : null}
      </div>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}
