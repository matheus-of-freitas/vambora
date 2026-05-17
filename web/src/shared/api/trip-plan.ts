import type { Schemas } from "./openapi";

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export interface LatLon {
  lat: number;
  lon: number;
}

// Generated from the backend OpenAPI schema (see openapi.ts / `pnpm gen:api`).
export type TripLeg = Schemas["LegDTO"];
export type Connection = Schemas["ConnectionDTO"];
export type Itinerary = Schemas["ItineraryDTO"];

// Refinement of the backend's `kind: string` (the ConnectionKind enum's
// serialized values) — purely for ergonomic comparisons in the UI.
export type ConnectionKind = "INTERLINE" | "TIGHT" | "OK";

export interface PlanTripRequest {
  origin: LatLon;
  destination: LatLon;
  departAt?: string;
  maxItineraries?: number;
}

export const planTrip = async (
  req: PlanTripRequest,
  options: { signal?: AbortSignal } = {},
): Promise<Itinerary[]> => {
  const response = await fetch(`${baseUrl()}/trips/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      origin: req.origin,
      destination: req.destination,
      depart_at: req.departAt ?? null,
      max_itineraries: req.maxItineraries ?? 3,
    }),
    signal: options.signal,
  });
  if (!response.ok) throw new Error(`trip plan: HTTP ${response.status}`);
  return (await response.json()) as Itinerary[];
};
