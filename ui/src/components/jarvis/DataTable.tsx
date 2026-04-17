import { cn } from "@/lib/utils";

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
  align?: "left" | "right" | "center";
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  empty?: string;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  empty = "No data.",
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={cn(
                  "px-3 py-2.5 font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-text-muted",
                  col.align === "right" && "text-right",
                  col.align === "center" && "text-center",
                  !col.align && "text-left",
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-8 text-center font-mono text-xs text-text-muted">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={i}
                className={cn(
                  "border-b border-border-light transition-colors hover:bg-bg-hover",
                  i % 2 === 1 && "bg-bg-tertiary/30",
                )}
              >
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className={cn(
                      "px-3 py-2.5 text-text-secondary",
                      col.align === "right" && "text-right",
                      col.align === "center" && "text-center",
                      col.className,
                    )}
                  >
                    {col.render ? col.render(row) : (row[col.key as keyof T] as React.ReactNode)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
