import { isAbort, offlineLineRealtime } from "@/shared/lib/offline";
import type { Schemas } from "./openapi";

// Generated from the backend OpenAPI schema (see openapi.ts / `pnpm gen:api`).
export type RouteSummary = Schemas["RouteDTO"];
export type LineRealtime = Schemas["LineRealtimeDTO"];

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export const fetchLineRealtime = async (
  shortName: string,
  options: { freshSeconds?: number; signal?: AbortSignal } = {},
): Promise<LineRealtime | null> => {
  const url = new URL(`${baseUrl()}/lines/${encodeURIComponent(shortName)}/realtime`);
  if (options.freshSeconds !== undefined) {
    url.searchParams.set("fresh_seconds", String(options.freshSeconds));
  }
  try {
    const response = await fetch(url, { signal: options.signal });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`line realtime: HTTP ${response.status}`);
    return (await response.json()) as LineRealtime;
  } catch (err) {
    if (isAbort(err)) throw err;
    // Offline: line metadata from the bundle, no live vehicles.
    const offline = await offlineLineRealtime(shortName);
    if (offline) return offline;
    throw err;
  }
};
