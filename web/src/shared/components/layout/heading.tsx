import { type VariantProps, cva } from "class-variance-authority";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

const headingVariants = cva("font-semibold tracking-tight", {
  variants: {
    variant: {
      display: "text-3xl",
      page: "text-base",
      section: "text-sm uppercase tracking-wider text-muted-foreground",
    },
  },
  defaultVariants: { variant: "page" },
});

type Level = 1 | 2 | 3;

interface HeadingProps
  extends ComponentPropsWithoutRef<"h1">,
    VariantProps<typeof headingVariants> {
  level?: Level;
  children: ReactNode;
}

const tagFor = (level: Level): "h1" | "h2" | "h3" =>
  (({ 1: "h1", 2: "h2", 3: "h3" }) as const)[level];

export const Heading = ({ level = 1, variant, className, children, ...rest }: HeadingProps) => {
  const Tag = tagFor(level);
  return (
    <Tag className={cn(headingVariants({ variant }), className)} {...rest}>
      {children}
    </Tag>
  );
};
