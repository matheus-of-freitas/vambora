import { type VariantProps, cva } from "class-variance-authority";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

const textVariants = cva("", {
  variants: {
    variant: {
      body: "text-sm leading-6",
      caption: "text-xs leading-5",
      label: "text-xs font-medium uppercase tracking-wider",
    },
    muted: {
      true: "text-muted-foreground",
      false: "",
    },
  },
  defaultVariants: { variant: "body", muted: false },
});

interface TextProps extends ComponentPropsWithoutRef<"p">, VariantProps<typeof textVariants> {
  children: ReactNode;
  as?: "p" | "span" | "div";
}

export const Text = ({
  variant,
  muted,
  as: Tag = "p",
  className,
  children,
  ...rest
}: TextProps) => (
  <Tag className={cn(textVariants({ variant, muted }), className)} {...rest}>
    {children}
  </Tag>
);
