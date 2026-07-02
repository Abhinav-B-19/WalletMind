type SectionTitleProps = {
  title: string;
  subtitle?: string;
};

export function PageTitle({ title, subtitle }: SectionTitleProps) {
  return (
    <header className="space-y-1">
      <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
        {title}
      </h2>
      {subtitle ? (
        <p className="text-sm text-[var(--text-muted)]">{subtitle}</p>
      ) : null}
    </header>
  );
}

export function SectionTitle({ title, subtitle }: SectionTitleProps) {
  return (
    <div className="space-y-1">
      <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
      {subtitle ? (
        <p className="text-sm text-[var(--text-muted)]">{subtitle}</p>
      ) : null}
    </div>
  );
}
