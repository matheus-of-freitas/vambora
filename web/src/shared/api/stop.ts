import { isAbort, offlineStop } from "@/shared/lib/offline";
import type { Stop } from "./stops";

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

export const fetchStop = async (
  stopId: string,
  options: { signal?: AbortSignal } = {},
): Promise<Stop | null> => {
  const url = new URL(`${baseUrl()}/stops/${encodeURIComponent(stopId)}`);
  try {
    const response = await fetch(url, { signal: options.signal });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`stops/{id}: HTTP ${response.status}`);
    return (await response.json()) as Stop;
  } catch (err) {
    if (isAbort(err)) throw err;
    const offline = await offlineStop(stopId);
    if (offline) return offline;
    throw err;
  }
};
