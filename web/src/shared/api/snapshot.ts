import type { Schemas } from "./openapi";

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

// SnapshotLatest is a backend DTO (generated). The OfflineBundle below is NOT
// an OpenAPI schema — it's the gzipped JSON blob the bundle endpoint streams,
// so it stays hand-defined.
export type SnapshotLatest = Schemas["SnapshotLatestDTO"];

export interface BundleRoute {
  route_id: string;
  short_name: string;
  long_name: string;
  color: string | null;
}

export interface BundleStop {
  stop_id: string;
  name: string;
  code: string | null;
  lat: number;
  lon: number;
}

export interface OfflineBundle {
  meta: {
    version: string;
    feed_version: string;
    generated_at: string;
    route_count: number;
    stop_count: number;
  };
  routes: BundleRoute[];
  stops: BundleStop[];
  // short_name -> list of polylines; each polyline is [lon, lat] pairs.
  line_shapes: Record<string, [number, number][][]>;
  headways: Record<string, number>;
  // stop_id -> sorted serving line short_names (offline schedule substitute).
  stop_lines: Record<string, string[]>;
}

export const fetchSnapshotLatest = async (
  options: { signal?: AbortSignal } = {},
): Promise<SnapshotLatest | null> => {
  const response = await fetch(`${baseUrl()}/snapshots/latest`, { signal: options.signal });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`snapshots/latest: HTTP ${response.status}`);
  return (await response.json()) as SnapshotLatest;
};

// The backend serves the bundle gzipped with Content-Encoding: gzip, so the
// browser inflates it transparently and this is plain JSON.
export const fetchBundle = async (
  url: string,
  options: { signal?: AbortSignal } = {},
): Promise<OfflineBundle> => {
  const response = await fetch(`${baseUrl()}${url}`, { signal: options.signal });
  if (!response.ok) throw new Error(`snapshot bundle: HTTP ${response.status}`);
  return (await response.json()) as OfflineBundle;
};
