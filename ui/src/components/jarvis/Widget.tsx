import * as React from "react";
import { cn } from "@/lib/utils";

interface WidgetProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  variant?: "default" | "elevated";
}

export const Widget = React.forwardRef<HTMLDivElement, WidgetProps>(
  ({ title, icon, action, variant = "default", className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "group relative overflow-hidden rounded-lg border border-border bg-bg-secondary transition-all",
          "hover:border-border-dark hover:shadow-hud-md",
          variant === "elevated" && "bg-bg-tertiary",
          className,
        )}
        {...props}
      >
        {/* Corner accents */}
        <span aria-hidden="true" className="pointer-events-none absolute left-0 top-0 h-2 w-2 border-l border-t border-accent/60" />
        <span aria-hidden="true" className="pointer-events-none absolute right-0 top-0 h-2 w-2 border-r border-t border-accent/60" />
        <span aria-hidden="true" className="pointer-events-none absolute bottom-0 left-0 h-2 w-2 border-b border-l border-accent/60" />
        <span aria-hidden="true" className="pointer-events-none absolute bottom-0 right-0 h-2 w-2 border-b border-r border-accent/60" />

        {title && (
          <div className="flex items-center justify-between gap-2 border-b border-border-light px-4 py-3">
            <div className="flex items-center gap-2 min-w-0">
              {icon && <span className="text-accent shrink-0">{icon}</span>}
              <h3 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-text-primary truncate">
                {title}
              </h3>
            </div>
            {action}
          </div>
        )}
        <div className={cn(title ? "p-4" : "p-5")}>{children}</div>
      </div>
    );
  },
);
Widget.displayName = "Widget";
