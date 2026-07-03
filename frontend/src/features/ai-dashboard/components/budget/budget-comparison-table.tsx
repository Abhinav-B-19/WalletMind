type BudgetComparisonRow = {
  category: string;
  current: number;
  recommended: number;
  difference: number;
  variancePercent: number;
  status: "within" | "near" | "over";
};

type BudgetComparisonTableProps = {
  rows: BudgetComparisonRow[];
  currencyFormatter: (value: number) => string;
};

const statusMap: Record<
  BudgetComparisonRow["status"],
  { label: string; className: string }
> = {
  within: { label: "Within Budget", className: "text-[#27c86f]" },
  near: { label: "Near Limit", className: "text-[#e3be37]" },
  over: { label: "Over Budget", className: "text-[#ff6a82]" },
};

export function BudgetComparisonTable({
  rows,
  currencyFormatter,
}: BudgetComparisonTableProps) {
  return (
    <div className="overflow-x-auto" aria-label="Budget comparison table">
      <table className="w-full min-w-[760px] border-separate border-spacing-y-2 text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-[var(--text-muted)]">
            <th className="px-3 py-2">Category</th>
            <th className="px-3 py-2">Current Spend</th>
            <th className="px-3 py-2">Recommended Budget</th>
            <th className="px-3 py-2">Difference</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Progress</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const status = statusMap[row.status];
            return (
              <tr
                key={row.category}
                className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] shadow-sm"
              >
                <td className="rounded-l-[var(--radius-md)] px-3 py-3 font-medium">
                  {row.category}
                </td>
                <td className="px-3 py-3">{currencyFormatter(row.current)}</td>
                <td className="px-3 py-3">
                  {currencyFormatter(row.recommended)}
                </td>
                <td className="px-3 py-3">
                  <span
                    className={
                      row.difference > 0 ? "text-[#ff6a82]" : "text-[#27c86f]"
                    }
                  >
                    {row.difference > 0 ? "+" : ""}
                    {currencyFormatter(row.difference)}
                  </span>
                </td>
                <td className={`px-3 py-3 font-medium ${status.className}`}>
                  {status.label}
                </td>
                <td className="rounded-r-[var(--radius-md)] px-3 py-3">
                  <div className="space-y-1">
                    <div
                      className="h-2 w-full overflow-hidden rounded-full bg-[var(--surface-soft)]"
                      role="progressbar"
                      aria-label={`${row.category} budget utilization`}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={Math.round(
                        Math.min(100, Math.max(0, row.variancePercent)),
                      )}
                    >
                      <div
                        className="h-full rounded-full bg-[#4f8df7]"
                        style={{
                          width: `${Math.min(100, Math.max(0, row.variancePercent))}%`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-[var(--text-muted)]">
                      {row.variancePercent.toFixed(0)}%
                    </p>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
