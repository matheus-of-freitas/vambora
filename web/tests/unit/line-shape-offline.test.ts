import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/storage/bundle", () => ({ getBundle: vi.fn() }));

import { fetchLineShape } from "@/shared/api/line-shape";
import { getBundle } from "@/shared/storage/bundle";

const mockedGetBundle = vi.mocked(getBundle);

const bundleWith485 = {
  meta: {
    version: "v1",
    feed_version: "f1",
    generated_at: "2026-05-16T00:00:00Z",
    route_count: 1,
    stop_count: 0,
  },
  routes: [],
  stops: [],
  line_shapes: {
    "485": [
      [
        [-43.2, -22.9],
        [-43.21, -22.91],
      ] as [number, number][],
    ],
  },
  headways: {},
  stop_lines: {},
};

describe("fetchLineShape offline fallback", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("returns network data when online (no bundle read)", async () => {
    const fc = { type: "FeatureCollection", features: [] };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(fc), { status: 200 })),
    );
    const result = await fetchLineShape("485");
    expect(result).toEqual(fc);
    expect(mockedGetBundle).not.toHaveBeenCalled();
  });

  it("falls back to the stored bundle when the network fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    mockedGetBundle.mockResolvedValue(bundleWith485);

    const result = await fetchLineShape("485");
    expect(result?.type).toBe("FeatureCollection");
    expect(result?.features).toHaveLength(1);
    expect(result?.features[0]?.geometry).toEqual({
      type: "LineString",
      coordinates: [
        [-43.2, -22.9],
        [-43.21, -22.91],
      ],
    });
  });

  it("rethrows when offline and the line is not in the bundle", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    mockedGetBundle.mockResolvedValue({ ...bundleWith485, line_shapes: {} });

    await expect(fetchLineShape("485")).rejects.toThrow();
  });
});
