import { getBundle } from "@/shared/storage/bundle";

// FeatureCollection of LineStrings — one per distinct shape on the line.
export type ShapeFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.LineString>;

const baseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8002";

const shapeFromBundle = async (shortName: string): Promise<ShapeFeatureCollection | null> => {
  const bundle = await getBundle();
  const polylines = bundle?.line_shapes[shortName];
  if (!polylines || polylines.length === 0) return null;
  return {
    type: "FeatureCollection",
    features: polylines.map((coords) => ({
      type: "Feature",
      geometry: { type: "LineString", coordinates: coords },
      properties: {},
    })),
  };
};

export const fetchLineShape = async (
  shortName: string,
  options: { signal?: AbortSignal } = {},
): Promise<ShapeFeatureCollection | null> => {
  const url = new URL(`${baseUrl()}/lines/${encodeURIComponent(shortName)}/shape`);
  try {
    const response = await fetch(url, { signal: options.signal });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`line shape: HTTP ${response.status}`);
    return (await response.json()) as ShapeFeatureCollection;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    // Network failed — serve the route geometry from the offline bundle.
    const offline = await shapeFromBundle(shortName);
    if (offline) return offline;
    throw err;
  }
};
