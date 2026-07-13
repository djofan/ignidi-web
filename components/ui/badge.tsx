import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-[var(--font-mono)] uppercase tracking-[0.14em] transition-colors",
  {
    variants: {
      variant: {
        default:
          "border-[var(--color-ember)]/40 bg-[var(--color-ember)]/10 text-[var(--color-ember)]",
        outline: "border-[var(--color-line)] text-[var(--color-slate)]",
        solid: "border-transparent bg-[var(--color-ember)] text-[var(--color-ink)]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
