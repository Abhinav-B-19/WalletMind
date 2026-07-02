export function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-xl rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-10 shadow-[var(--shadow-md)]">
        <div className="flex items-center gap-3">
          <div className="h-3 w-3 animate-pulse rounded-full bg-[var(--primary)]" />
          <p className="text-sm font-medium text-[var(--text-muted)]">
            Loading WalletMind workspace...
          </p>
        </div>
      </div>
    </div>
  );
}
