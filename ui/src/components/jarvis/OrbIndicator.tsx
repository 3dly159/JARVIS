import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { ORB_COLORS, ORB_LABELS, type OrbState } from "@/hooks/useOrbState";

interface OrbIndicatorProps {
  state: OrbState;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

const SIZES = {
  sm: "h-2.5 w-2.5",
  md: "h-3.5 w-3.5",
  lg: "h-5 w-5",
};

export function OrbIndicator({ state, size = "md", showLabel = false, className }: OrbIndicatorProps) {
  const [bump, setBump] = useState(0);
  useEffect(() => setBump((b) => b + 1), [state]);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        key={bump}
        role="status"
        aria-label={`Orb state: ${ORB_LABELS[state]}`}
        className={cn(
          "inline-block rounded-full animate-pulse-orb animate-orb-bump",
          SIZES[size],
        )}
        style={{
          backgroundColor: ORB_COLORS[state],
          color: ORB_COLORS[state],
        }}
      />
      {showLabel && (
        <span className="font-mono text-xs uppercase tracking-widest text-text-secondary">
          {ORB_LABELS[state]}
        </span>
      )}
    </div>
  );
}
