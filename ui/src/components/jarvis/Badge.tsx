import { cn } from "@/lib/utils";

type BadgeVariant = "success" | "warning" | "error" | "info" | "neutral";

const VARIANTS: Record<BadgeVariant, string> = {
  success: "border-success/40 bg-success/10 text-success",
  warning: "border-warning/40 bg-warning/10 text-warning",
  error: "border-error/40 bg-error/10 text-error",
  info: "border-info/40 bg-info/10 text-info",
  neutral: "border-border bg-bg-tertiary text-text-secondary",
};

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

export function JBadge({ variant = "neutral", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        VARIANTS[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
