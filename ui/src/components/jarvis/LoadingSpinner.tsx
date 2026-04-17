import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  size?: number;
  className?: string;
  label?: string;
}

export function LoadingSpinner({ size = 24, className, label = "Loading" }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn("inline-block", className)}
      style={{ width: size, height: size }}
    >
      <svg viewBox="0 0 50 50" className="h-full w-full animate-spin" style={{ color: "var(--accent)" }}>
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeOpacity="0.2"
          strokeWidth="3"
        />
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="80 50"
          style={{ filter: "drop-shadow(0 0 4px currentColor)" }}
        />
      </svg>
    </div>
  );
}
