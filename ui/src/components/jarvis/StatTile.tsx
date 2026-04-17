import { cn } from "@/lib/utils";
import { Widget } from "./Widget";

interface StatTileProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: { value: string; trend: "up" | "down" | "flat" };
  icon?: React.ReactNode;
  accentColor?: string;
}

export function StatTile({ label, value, unit, delta, icon, accentColor }: StatTileProps) {
  const trendColor =
    delta?.trend === "up"
      ? "text-success"
      : delta?.trend === "down"
        ? "text-error"
        : "text-text-muted";

  return (
    <Widget className="relative">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-muted">{label}</p>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span
              className="font-display text-3xl font-semibold leading-none text-text-primary tabular-nums"
              style={accentColor ? { color: accentColor } : undefined}
            >
              {value}
            </span>
            {unit && <span className="font-mono text-xs text-text-muted">{unit}</span>}
          </div>
          {delta && (
            <p className={cn("mt-2 font-mono text-[11px] uppercase tracking-wider", trendColor)}>
              {delta.trend === "up" ? "▲" : delta.trend === "down" ? "▼" : "■"} {delta.value}
            </p>
          )}
        </div>
        {icon && (
          <div className="rounded-md border border-border-light bg-bg-tertiary p-2 text-accent">
            {icon}
          </div>
        )}
      </div>
    </Widget>
  );
}
