# vambora-docs

Documentation site for Vambora. Docusaurus 3 with Mermaid C4 diagrams. Deploys to Cloudflare Pages at `vambora-docs.pages.dev` (custom `docs.vambora.app` is deferred).

## Run

```bash
pnpm install
pnpm start          # dev server with HMR on :3000
pnpm build          # production build to ./build
pnpm typecheck      # tsc strict
pnpm serve          # serve the production build locally
```

## Authoring

- Pages live under `docs/`. Sidebar order is set in `sidebars.ts`.
- Diagrams are Mermaid in fenced code blocks. C4 syntax is supported.
- Internal links must resolve at build time — `onBrokenLinks: "throw"` is set.

## Deploy

Connected to **Cloudflare Pages via the dashboard (Connect to Git)** on the
single `vambora` monorepo with **Root directory `docs`** (project
`vambora-docs`, build `pnpm build`, output `build`). Cloudflare builds and
redeploys on every push to `main`. **No GitHub secrets, no API token, no
DNS** while the domain is deferred. (Step-by-step provisioning/deploy
runbooks are kept as internal notes, not published here.) `ci.yml` still
runs typecheck/build checks on PRs.
