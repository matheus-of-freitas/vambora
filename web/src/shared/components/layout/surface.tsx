import { type VariantProps, cva } from "class-variance-authority";
import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

const surfaceVariants = cva("rounded-md", {
  variants: {
    elevation: {
      flat: "bg-card text-card-foreground",
      raised: "bg-card text-card-foreground shadow",
    },
    overlay: {
      true: "bg-card/90 backdrop-blur-sm shadow",
      false: "",
    },
    padding: {
      none: "",
      sm: "px-3 py-2",
      md: "p-4",
      lg: "p-6",
    },
  },
  defaultVariants: { elevation: "raised", overlay: false, padding: "sm" },
});

interface SurfaceProps
  extends ComponentPropsWithoutRef<"div">,
    VariantProps<typeof surfaceVariants> {
  children: ReactNode;
}

export const Surface = ({
  elevation,
  overlay,
  padding,
  className,
  children,
  ...rest
}: SurfaceProps) => (
  <div className={cn(surfaceVariants({ elevation, overlay, padding }), className)} {...rest}>
    {children}
  </div>
);
