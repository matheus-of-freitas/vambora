import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/storage/bundle", () => ({ getBundle: vi.fn() }));

import { fetchLineRealtime } from "@/shared/api/line-realtime";
import { fetchStop } from "@/shared/api/stop";
import { fetchNearbyStops } from "@/shared/api/stops";
import { offlineStopLines } from "@/shared/lib/offline";
import { getBundle } from "@/shared/storage/bundle";

const mockedGetBundle = vi.mocked(getBundle);

const bundle = {
  meta: {
    version: "v1",
    feed_version: "f1",
    generated_at: "2026-05-16T00:00:00Z",
    route_count: 1,
    stop_count: 2,
  },
  routes: [{ route_id: "R485", short_name: "485", long_name: "Gávea–Centro", color: "FCC417" }],
  stops: [
    { stop_id: "S1", name: "Perto", code: null, lat: -22.9, lon: -43.2 },
    { stop_id: "S2", name: "Longe", code: "C2", lat: -22.99, lon: -43.35 },
  ],
  line_shapes: {},
  headways: { "485": 1200, "100": 59 },
  stop_lines: { S1: ["485", "100", "999"] },
};

const networkFail = () =>
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    }),
  );

describe("offline fallbacks", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("fetchStop falls back to the bundle stop", async () => {
    networkFail();
    mockedGetBundle.mockResolvedValue(bundle);
    const stop = await fetchStop("S1");
    expect(stop).toMatchObject({
      stop_id: "S1",
      name: "Perto",
      latitude: -22.9,
      longitude: -43.2,
      parent_station: null,
    });
  });

  it("fetchStop rethrows when stop not in bundle", async () => {
    networkFail();
    mockedGetBundle.mockResolvedValue(bundle);
    await expect(fetchStop("UNKNOWN")).rejects.toThrow();
  });

  it("fetchNearbyStops returns bundle stops nearest-first", async () => {
    networkFail();
    mockedGetBundle.mockResolvedValue(bundle);
    const near = await fetchNearbyStops({ lat: -22.9, lon: -43.2, radiusM: 100_000 });
    expect(near.map((s) => s.stop_id)).toEqual(["S1", "S2"]);
  });

  it("fetchLineRealtime returns bundle route metadata, no vehicles", async () => {
    networkFail();
    mockedGetBundle.mockResolvedValue(bundle);
    const rt = await fetchLineRealtime("485");
    expect(rt?.vehicles).toEqual([]);
    expect(rt?.routes[0]).toMatchObject({ short_name: "485", long_name: "Gávea–Centro" });
  });

  it("fetchLineRealtime rethrows for an unknown line", async () => {
    networkFail();
    mockedGetBundle.mockResolvedValue(bundle);
    await expect(fetchLineRealtime("000")).rejects.toThrow();
  });

  it("offlineStopLines maps headway seconds to whole minutes (min 1)", async () => {
    mockedGetBundle.mockResolvedValue(bundle);
    const lines = await offlineStopLines("S1");
    expect(lines).toEqual([
      { short_name: "485", headway_minutes: 20 },
      { short_name: "100", headway_minutes: 1 }, // 59s -> floor would be 0; clamped to 1
      { short_name: "999", headway_minutes: null }, // no headway entry
    ]);
  });
});
