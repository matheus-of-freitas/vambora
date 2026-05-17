import { isAbort, offlineNearbyStops } from "@/shared/lib/offline";
import type { Schemas } from "./openapi";

// Generated from the backend OpenAPI schema (see openapi.ts / `pnpm gen:api`).
export type Stop = Schemas["StopDTO"];

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export interface FetchNearbyStopsParams {
  lat: number;
  lon: number;
  radiusM?: number;
  limit?: number;
  signal?: AbortSignal;
}

export const fetchNearbyStops = async (params: FetchNearbyStopsParams): Promise<Stop[]> => {
  const url = new URL(`${baseUrl()}/stops/nearby`);
  url.searchParams.set("lat", String(params.lat));
  url.searchParams.set("lon", String(params.lon));
  if (params.radiusM !== undefined) url.searchParams.set("radius_m", String(params.radiusM));
  if (params.limit !== undefined) url.searchParams.set("limit", String(params.limit));
  try {
    const response = await fetch(url, { signal: params.signal });
    if (!response.ok) throw new Error(`stops/nearby: HTTP ${response.status}`);
    return (await response.json()) as Stop[];
  } catch (err) {
    if (isAbort(err)) throw err;
    // Offline: nearest stops from the bundle (empty list is acceptable).
    return offlineNearbyStops(params.lat, params.lon, params.radiusM ?? 500, params.limit ?? 200);
  }
};
