import * as React from "react";
import { cn } from "@/lib/utils";

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant?: "ghost" | "outlined";
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ label, variant = "ghost", className, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        aria-label={label}
        title={label}
        className={cn(
          "inline-flex h-9 w-9 items-center justify-center rounded-md text-text-secondary transition-all",
          "hover:bg-bg-hover hover:text-accent",
          "active:scale-95 active:bg-bg-active",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg-secondary",
          variant === "outlined" && "border border-border",
          className,
        )}
        {...props}
      >
        {children}
      </button>
    );
  },
);
IconButton.displayName = "IconButton";
