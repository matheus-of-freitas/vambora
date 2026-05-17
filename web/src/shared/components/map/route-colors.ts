// Single bridge between the design-system color tokens and MapLibre paint
// expressions. MapLibre's `paint` properties don't accept `var(--…)` references,
// so we mirror the HSL values from `globals.css` here. If a token's HSL changes
// in `globals.css`, change it here too. The kitchen-sink page renders these
// next to a Tailwind `bg-route-bus` swatch so the drift is visible.
export const ROUTE_COLORS = {
  bus: "hsl(43, 96%, 56%)",
  brt: "hsl(217, 91%, 60%)",
  vlt: "hsl(142, 71%, 45%)",
  // Neutral for non-transit (walking) legs in the trip planner.
  walk: "hsl(215, 20%, 65%)",
} as const;

export type RouteKind = keyof typeof ROUTE_COLORS;
