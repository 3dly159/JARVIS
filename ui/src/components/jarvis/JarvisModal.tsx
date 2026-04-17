import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { IconButton } from "./IconButton";

interface JarvisModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function JarvisModal({ open, onClose, title, description, children, footer }: JarvisModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    previousFocus.current = document.activeElement as HTMLElement;
    dialogRef.current?.focus();

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
      previousFocus.current?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center px-4 animate-fade-in"
      role="presentation"
    >
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="jarvis-modal-title"
        aria-describedby={description ? "jarvis-modal-desc" : undefined}
        tabIndex={-1}
        className={cn(
          "relative z-10 w-full max-w-lg overflow-hidden rounded-lg border border-border-dark bg-bg-secondary shadow-hud-lg animate-fade-scale-in",
          "focus:outline-none",
        )}
      >
        {/* Corner accents */}
        <span aria-hidden="true" className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l-2 border-t-2 border-accent" />
        <span aria-hidden="true" className="pointer-events-none absolute right-0 top-0 h-3 w-3 border-r-2 border-t-2 border-accent" />
        <span aria-hidden="true" className="pointer-events-none absolute bottom-0 left-0 h-3 w-3 border-b-2 border-l-2 border-accent" />
        <span aria-hidden="true" className="pointer-events-none absolute bottom-0 right-0 h-3 w-3 border-b-2 border-r-2 border-accent" />

        <div className="flex items-start justify-between gap-3 border-b border-border-light px-5 py-4">
          <div>
            <h2 id="jarvis-modal-title" className="font-display text-base font-semibold uppercase tracking-[0.18em] text-text-primary">
              {title}
            </h2>
            {description && (
              <p id="jarvis-modal-desc" className="mt-1 font-mono text-xs text-text-muted">
                {description}
              </p>
            )}
          </div>
          <IconButton label="Close dialog" onClick={onClose}>
            <X className="h-4 w-4" />
          </IconButton>
        </div>

        <div className="px-5 py-5">{children}</div>

        {footer && <div className="flex justify-end gap-2 border-t border-border-light bg-bg-primary/40 px-5 py-3">{footer}</div>}
      </div>
    </div>
  );
}
