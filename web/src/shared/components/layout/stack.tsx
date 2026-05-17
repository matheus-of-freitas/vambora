import { type VariantProps, cva } from "class-variance-authority";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

const stackVariants = cva("flex", {
  variants: {
    direction: {
      row: "flex-row items-center",
      col: "flex-col",
    },
    gap: {
      xs: "gap-1",
      sm: "gap-2",
      md: "gap-4",
      lg: "gap-6",
    },
    align: {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
    },
    justify: {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
    },
  },
  defaultVariants: { direction: "col", gap: "md" },
});

interface StackProps extends ComponentPropsWithoutRef<"div">, VariantProps<typeof stackVariants> {
  children: ReactNode;
}

export const Stack = ({
  direction,
  gap,
  align,
  justify,
  className,
  children,
  ...rest
}: StackProps) => (
  <div className={cn(stackVariants({ direction, gap, align, justify }), className)} {...rest}>
    {children}
  </div>
);
