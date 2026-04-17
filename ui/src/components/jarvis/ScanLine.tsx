/**
 * Decorative scan-line overlay for the HUD.
 * Pointer-events: none — purely visual.
 */
export function ScanLine() {
  return (
    <div className="pointer-events-none fixed inset-0 z-[5] overflow-hidden" aria-hidden="true">
      <div
        className="absolute inset-x-0 h-[2px] animate-scan-line"
        style={{
          background:
            "linear-gradient(90deg, transparent, oklch(0.72 0.18 230 / 0.4), transparent)",
          boxShadow: "0 0 16px oklch(0.72 0.18 230 / 0.5)",
        }}
      />
    </div>
  );
}
