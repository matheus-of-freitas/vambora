---
sidebar_position: 1
---

# Tokens

The single source of truth for color, spacing, radius, and elevation across `vambora-web`. Tokens are CSS variables in `web/src/app/globals.css`. Tailwind theme references the variables; shadcn components consume them; **feature code never reaches for raw hex**.

When `vambora-android` arrives, its Material 3 theme mirrors the same hex values — the documented values here are the contract.

## Surface (dark)

| Token | HSL | Hex (approx) | Use |
|---|---|---|---|
| `--background` | `240 10% 4%` | `#09090b` | App body background |
| `--foreground` | `0 0% 98%` | `#fafafa` | Default text |
| `--card` | `240 6% 10%` | `#18181b` | Card / surface fill |
| `--card-foreground` | `0 0% 98%` | `#fafafa` | Text on card |
| `--popover` | `240 6% 10%` | `#18181b` | Popover / dropdown fill |
| `--secondary` | `240 4% 16%` | `#27272a` | Secondary chrome |
| `--muted` | `240 4% 16%` | `#27272a` | Disabled, hint surfaces |
| `--muted-foreground` | `240 5% 65%` | `#a1a1aa` | Subdued text |
| `--border` | `240 4% 16%` | `#27272a` | All borders |
| `--input` | `240 4% 16%` | `#27272a` | Form control borders |
| `--ring` | `43 96% 56%` | `#fbbf24` | Focus rings (= primary) |

## Brand / route

| Token | HSL | Hex | Modal |
|---|---|---|---|
| `--route-bus` | `43 96% 56%` | `#fbbf24` | City buses (SPPO) |
| `--route-brt` | `217 91% 60%` | `#3b82f6` | BRT (TransOeste, TransCarioca, etc.) |
| `--route-vlt` | `142 71% 45%` | `#22c55e` | VLT (light rail) |

## Semantic

| Token | Maps to | Use |
|---|---|---|
| `--primary` | `--route-bus` | Primary CTAs, focus ring; bus is the dominant modal |
| `--accent` | `--route-brt` | Highlights, secondary CTAs |
| `--destructive` | `0 72% 51%` (`#dc2626`) | Errors, irreversible actions |

## Spacing

Use the Tailwind scale (`gap-1`, `gap-2`, `gap-4`, `gap-6`, …) **only via the `<Stack>` primitive's `gap` prop** when you can. The mapping:

| Stack `gap` | Tailwind | rem |
|---|---|---|
| `xs` | `gap-1` | 0.25 |
| `sm` | `gap-2` | 0.5 |
| `md` | `gap-4` | 1 |
| `lg` | `gap-6` | 1.5 |

Padding and margin go through the Tailwind scale directly (`p-2`, `px-4`). **Arbitrary values like `p-[13px]` are forbidden** — see `lint:design`.

## Radius

| Token | Value | Tailwind |
|---|---|---|
| `--radius` | `0.5rem` | `rounded-md` (default) |

## Typography

No custom typography variables — the Tailwind scale is enough. Use the `<Heading>` and `<Text>` primitives to apply it consistently:

| Component | Variant | Tailwind |
|---|---|---|
| `Heading` | `display` | `text-3xl font-semibold tracking-tight` |
| `Heading` | `page` | `text-base font-semibold tracking-tight` |
| `Heading` | `section` | `text-sm uppercase tracking-wider text-muted-foreground` |
| `Text` | `body` | `text-sm leading-6` |
| `Text` | `caption` | `text-xs leading-5` |
| `Text` | `label` | `text-xs font-medium uppercase tracking-wider` |

## MapLibre bridge

MapLibre's `paint` properties don't accept `var(--…)` references, so the route colors are mirrored as a TS constant in `web/src/shared/components/map/route-colors.ts`. If a token's HSL changes in `globals.css`, **change it there too**. The kitchen-sink page renders both side-by-side so drift is visible.

## Themes (color modes)

MVP ships dark only. The `:root` and `.dark` blocks in `globals.css` are intentionally identical right now. Light theme arrives in Phase 2 — see `plan.md` non-goals.
