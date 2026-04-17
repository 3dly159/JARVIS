import { useEffect, useState } from "react";

export type OrbState = "idle" | "listening" | "speaking" | "thinking" | "error";

export const ORB_COLORS: Record<OrbState, string> = {
  idle: "var(--accent)",
  listening: "var(--info)",
  speaking: "var(--success)",
  thinking: "var(--warning)",
  error: "var(--error)",
};

export const ORB_LABELS: Record<OrbState, string> = {
  idle: "Standby",
  listening: "Listening",
  speaking: "Speaking",
  thinking: "Processing",
  error: "Fault",
};

/**
 * Tracks orb state and emits a brief "bump" trigger on each change so the
 * indicator can play a 150ms scale animation.
 */
export function useOrbState(state: OrbState) {
  const [bumpKey, setBumpKey] = useState(0);

  useEffect(() => {
    setBumpKey((k) => k + 1);
  }, [state]);

  return {
    color: ORB_COLORS[state],
    label: ORB_LABELS[state],
    bumpKey,
  };
}
