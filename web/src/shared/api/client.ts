import type { VehiclePosition } from "./types";

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export interface FetchVehiclesParams {
  freshSeconds?: number;
  lineId?: string;
  signal?: AbortSignal;
}

export const fetchVehicles = async (
  params: FetchVehiclesParams = {},
): Promise<VehiclePosition[]> => {
  const url = new URL(`${baseUrl()}/vehicles`);
  if (params.freshSeconds !== undefined) {
    url.searchParams.set("fresh_seconds", String(params.freshSeconds));
  }
  if (params.lineId) {
    url.searchParams.set("line_id", params.lineId);
  }
  const response = await fetch(url, { signal: params.signal });
  if (!response.ok) {
    throw new Error(`vehicles: HTTP ${response.status}`);
  }
  return (await response.json()) as VehiclePosition[];
};
