import type { Schemas } from "./openapi";

// Generated from the backend OpenAPI schema (see openapi.ts / `pnpm gen:api`).
export type ArrivalPrediction = Schemas["PredictionDTO"];

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export const fetchStopPredictions = async (
  stopId: string,
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<ArrivalPrediction[]> => {
  const url = new URL(`${baseUrl()}/stops/${encodeURIComponent(stopId)}/predictions`);
  if (options.limit !== undefined) url.searchParams.set("limit", String(options.limit));
  const response = await fetch(url, { signal: options.signal });
  if (!response.ok) throw new Error(`stops/{id}/predictions: HTTP ${response.status}`);
  return (await response.json()) as ArrivalPrediction[];
};
