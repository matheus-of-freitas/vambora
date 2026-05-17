# vambora-web

Next.js 15 PWA for Vambora. MapLibre GL map of Rio de Janeiro, live bus tracking via the backend at `localhost:8002` (see `../backend/`).

## Run

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

Make sure the backend is up: `cd ../backend && docker compose up -d && uv run python -m vambora.main`. Open <http://localhost:3000>.

## Quality gates

```bash
pnpm lint        # Biome
pnpm typecheck   # tsc --noEmit, strict
pnpm test        # Vitest unit
pnpm e2e         # Playwright
pnpm build
```

## Conventions

Per `../plan.md` §"Working Conventions" and `../backend/docs/adrs/0001-hexagonal-architecture.md`:

- `src/app/` — Next.js routes only, thin orchestration.
- `src/features/<feature>/` — feature-sliced modules with their own `api/`, `components/`, `hooks/`, `store/`.
- `src/shared/` — design system primitives, MapLibre wrappers, the OpenAPI client (later), i18n messages.
- All user-facing strings come from `messages/pt-BR.json` via `next-intl`. No hardcoded Portuguese in JSX.
- TypeScript strict everywhere; no `any`, no `@ts-ignore` without comment.
