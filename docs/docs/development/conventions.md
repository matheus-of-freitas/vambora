---
sidebar_position: 2
---

# Conventions

Hard rules. The CI gates enforce most of them; the rest are review discipline.

## All repos

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`.
- **One task per branch**, one PR.
- **Squash and merge**.
- **Update relevant ADRs and docs in the same PR** as the code change.
- **No silent design decisions**: write or update an ADR and reference it from the PR description.

## Backend (Python)

- **Hexagonal discipline**:
  - `domain/` imports only from the standard library, `pydantic`, and typing tools. No SQLAlchemy, no FastAPI, no HTTP clients.
  - `application/` orchestrates `domain` + `ports`.
  - `adapters/` implements `ports/` interfaces and may depend on third-party libraries.
- **Strict typing**: `mypy --strict` is the baseline. No `Any` without a comment.
- **Async by default** for I/O. Sync only when explicitly justified.
- **Errors**: every error inherits from a context-specific base (`TrackingError`, `ProviderError`, etc.).
- **Logging**: `structlog` with structured key-value pairs. Never log secrets.

## Web (TypeScript)

- **TypeScript strict** is non-negotiable. No `any`, no `@ts-ignore` without a comment.
- **API payload types are generated, not hand-written.** Run `pnpm gen:api` (point `NEXT_PUBLIC_API_BASE_URL` at the backend; defaults to `http://localhost:8002`) to regenerate `src/shared/api/schema.d.ts` from the live OpenAPI schema. DTO types are re-exported from it via `src/shared/api/openapi.ts` (e.g. `export type Stop = Schemas["StopDTO"]`); never hand-declare a type that mirrors a backend DTO. The bespoke `fetch` wrappers (offline fallbacks, gzip, error mapping) stay hand-written by design — only the *types* are generated. After a backend DTO change: regenerate, then `pnpm typecheck` — a mismatch is now a compile error, not a runtime surprise. `schema.d.ts` is committed (so typecheck/CI need no running backend) and Biome-ignored.
- **Server vs client components**: prefer server components; mark `"use client"` only when needed.
- **Feature-sliced**: new features go under `src/features/<name>/` with their own `api/`, `components/`, `hooks/`.
- **Map components live under `src/shared/components/map/`** as MapLibre wrappers; no direct MapLibre calls in feature code.
- **i18n**: every user-facing string comes from `messages/pt-BR.json` via `next-intl`. No hardcoded Portuguese in JSX.

## Design system (web)

The design system is a closed inventory documented at [Design / Components](../design/components.md). Tokens (colors, spacing, radius, typography) live as CSS variables in `web/src/app/globals.css` and are documented at [Design / Tokens](../design/tokens.md).

Hard rules, enforced in CI by `pnpm lint:design`:

- **No raw colors in feature code**: no hex literals, no `rgb()/hsl()` strings, no `bg-[#…]` or `text-[#…]` arbitrary Tailwind classes. Use a token. If the token doesn't exist, define it in `globals.css` first.
- **No arbitrary Tailwind values for spacing/sizing**: no `p-[13px]`, `text-[15px]`, `gap-[7px]`. Use the Tailwind scale or the `<Stack>`/`<Heading>`/`<Text>` primitives.
- **No raw `flex`/`grid` containers in feature code**: use `<Stack>`. If the layout shape isn't there, add a `<Stack>` variant.
- **No raw `<h1..h6>`/`<p>` typography in feature code**: use `<Heading>` and `<Text>`.
- **The component inventory is closed**: adding a new component requires updating `docs/design/components.md` and the kitchen sink at `web/src/app/design/page.tsx` in the same PR.
- **One color mode for MVP**: dark only. Light theme arrives in Phase 2.

PRs touching the design system include before/after screenshots from `/design`.

The shadcn-vendored components in `web/src/shared/components/ui/` are exempt from these grep rules — we own them but they ship with their own internal styling.

## Forbidden

- Scraping Moovit, Waze, Google Maps, Cittamobi, or any commercial transit app.
- Storing personal data on the server (favorites stay on device until Phase 2 optional login).
- Committing secrets (`.env.example` documents required vars; real values go in CI secrets and server env).
- iOS code, React Native, or Android Auto support without explicit re-decision.

## Documentation

- **Update docs in the same PR** as code changes.
- **Diagrams as code**: Mermaid only, no binary images for architecture.
- Every REST endpoint has at least one request/response example in the OpenAPI spec.
