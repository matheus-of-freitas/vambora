// Single source of truth for API payload types: generated from the backend's
// OpenAPI schema (`pnpm gen:api` → schema.d.ts). Re-run gen:api after backend
// DTO changes; `pnpm typecheck` then proves the web is in sync (a mismatch
// becomes a compile error instead of a runtime surprise).
import type { components } from "./schema";

export type Schemas = components["schemas"];
