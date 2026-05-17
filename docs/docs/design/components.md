---
sidebar_position: 2
---

# Component inventory

This is the **closed inventory** of approved primitives and components for `vambora-web`. New UI must compose from this set or extend it via PR (with kitchen-sink update in the same PR).

The kitchen-sink page renders every entry below in every variant. Run it locally:

```bash
cd web && pnpm dev
# open http://localhost:3000/design
```

## Layout primitives

Hand-written in `web/src/shared/components/layout/`. Type-safe variants via `class-variance-authority`.

| Component | Path | Variants |
|---|---|---|
| `<Heading>` | `layout/heading.tsx` | `level={1\|2\|3}`, `variant="display"\|"page"\|"section"` |
| `<Text>` | `layout/text.tsx` | `variant="body"\|"caption"\|"label"`, `muted?`, `as="p"\|"span"\|"div"` |
| `<Stack>` | `layout/stack.tsx` | `direction="row"\|"col"`, `gap="xs"\|"sm"\|"md"\|"lg"`, `align`, `justify` |
| `<Surface>` | `layout/surface.tsx` | `elevation="flat"\|"raised"`, `overlay?`, `padding="none"\|"sm"\|"md"\|"lg"` |

`Surface(overlay)` is the recurring "translucent card floating over the map" pattern — used by the page header and `StatusBar`.

## Shadcn primitives

Vendored via `pnpm dlx shadcn@latest add`. Live in `web/src/shared/components/ui/`. We **own** these files and may edit them — but tweaks should serve the whole inventory, not a single feature.

| Component | Path | Notes |
|---|---|---|
| `<Button>` | `ui/button.tsx` | Variants: default, secondary, outline, ghost, destructive, link. Sizes: sm, default, lg, icon |
| `<Card>` (+ `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`) | `ui/card.tsx` | Used for line/stop summaries |
| `<Badge>` | `ui/badge.tsx` | Variants: default, secondary, outline, destructive |
| `<Skeleton>` | `ui/skeleton.tsx` | Loading placeholder |
| `<ScrollArea>` | `ui/scroll-area.tsx` | Constrained-height scroll containers |
| `<Input>` | `ui/input.tsx` | Single-line text input |

## Feature components

Live under `web/src/shared/components/ui/` (legacy from before shadcn) or `web/src/features/<name>/components/` going forward.

| Component | Path | Composes |
|---|---|---|
| `<StatusBar>` | `ui/status-bar.tsx` | `Surface(overlay)`, `Skeleton`, `Text(caption)` |
| `<LiveVehiclesMap>` | `map/live-vehicles-map.tsx` | MapLibre GL, uses `ROUTE_COLORS.bus` (token bridge) |

## Adding a new component

1. Decide whether it's a layout primitive (composable, generic) or a feature component (single-use).
2. If a primitive: add to `layout/` with `cva` variants, then update this page **and** add a section to `web/src/app/design/page.tsx`.
3. If a feature component: build under `features/<name>/components/`, compose from existing primitives. If a primitive doesn't exist for what you need, go back to step 2.
4. PR description must include before/after screenshots from `/design`.
5. CI runs `lint:design` and `pnpm typecheck`. The lint job rejects raw hex codes and arbitrary Tailwind values like `bg-[#…]`.

## What's intentionally not here yet

Add when the first feature using them lands — keeping the inventory closed prevents premature additions.

- Form controls: `Label`, `Select`, `Form`, `RadioGroup`, `Checkbox`, `Switch`.
- Overlays: `Dialog`, `Sheet`, `Toast`, `Tooltip`, `Popover`, `DropdownMenu`.
- Navigation: `Tabs`, `NavigationMenu`, `Breadcrumb`.
- Display: `Avatar`, `Separator`, `Accordion`, `Table`.

When you need one, run `pnpm dlx shadcn@latest add <name>`, update this page, update the kitchen sink.
