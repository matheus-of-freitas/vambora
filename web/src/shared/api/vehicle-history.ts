import type { VehiclePosition } from "./types";

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export const fetchVehicleHistory = async (
  vehicleId: string,
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<VehiclePosition[]> => {
  const url = new URL(`${baseUrl()}/vehicles/${encodeURIComponent(vehicleId)}`);
  if (options.limit !== undefined) url.searchParams.set("limit", String(options.limit));
  const response = await fetch(url, { signal: options.signal });
  if (response.status === 404) return [];
  if (!response.ok) throw new Error(`vehicle history: HTTP ${response.status}`);
  return (await response.json()) as VehiclePosition[];
};
