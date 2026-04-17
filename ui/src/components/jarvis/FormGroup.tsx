import * as React from "react";
import { cn } from "@/lib/utils";

interface FormGroupProps {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormGroup({ label, htmlFor, hint, children, className }: FormGroupProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <label
        htmlFor={htmlFor}
        className="block font-mono text-[10px] uppercase tracking-[0.2em] text-text-muted"
      >
        {label}
      </label>
      {children}
      {hint && <p className="font-mono text-[11px] text-text-muted">{hint}</p>}
    </div>
  );
}

const inputStyles =
  "w-full rounded-md border border-border bg-bg-primary px-3 py-2 font-sans text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30";

export const JInput = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={cn(inputStyles, className)} {...props} />
  ),
);
JInput.displayName = "JInput";

export const JTextarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea ref={ref} className={cn(inputStyles, "min-h-[88px] resize-y", className)} {...props} />
  ),
);
JTextarea.displayName = "JTextarea";

export const JSelect = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select ref={ref} className={cn(inputStyles, "appearance-none pr-8", className)} {...props}>
      {children}
    </select>
  ),
);
JSelect.displayName = "JSelect";

interface JSwitchProps {
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
  id?: string;
  label?: string;
}

export function JSwitch({ checked, onCheckedChange, id, label }: JSwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      id={id}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg-secondary",
        checked
          ? "border-accent bg-accent/30"
          : "border-border bg-bg-tertiary",
      )}
    >
      <span
        className={cn(
          "pointer-events-none inline-block h-4 w-4 transform rounded-full transition-transform",
          checked
            ? "translate-x-6 bg-accent shadow-[0_0_10px_var(--accent)]"
            : "translate-x-1 bg-text-muted",
        )}
      />
    </button>
  );
}

interface JButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
}

export const JButton = React.forwardRef<HTMLButtonElement, JButtonProps>(
  ({ variant = "primary", size = "md", className, ...props }, ref) => {
    const variants = {
      primary:
        "border-accent bg-accent/15 text-accent hover:bg-accent/25 active:bg-accent/30",
      secondary:
        "border-border bg-bg-tertiary text-text-primary hover:border-border-dark hover:bg-bg-active",
      ghost:
        "border-transparent bg-transparent text-text-secondary hover:bg-bg-hover hover:text-text-primary",
      danger:
        "border-error/50 bg-error/10 text-error hover:bg-error/20",
    };
    const sizes = {
      sm: "h-8 px-3 text-xs",
      md: "h-9 px-4 text-sm",
    };
    return (
      <button
        ref={ref}
        type="button"
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-md border font-display font-medium uppercase tracking-wider transition-all",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg-secondary",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "active:scale-[0.97]",
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      />
    );
  },
);
JButton.displayName = "JButton";
