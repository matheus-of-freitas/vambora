import { fetchVehicles } from "@/shared/api/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const sample = [
  {
    vehicle_id: "B11622",
    line_id: "363",
    recorded_at: "2026-05-09T14:00:00Z",
    sent_at: "2026-05-09T14:00:01Z",
    received_at: "2026-05-09T14:00:02Z",
    latitude: -22.9,
    longitude: -43.2,
    speed_kmh: 0,
  },
];

describe("fetchVehicles", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify(sample), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
      ),
    );
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed positions", async () => {
    const data = await fetchVehicles({ freshSeconds: 120 });
    expect(data).toHaveLength(1);
    expect(data[0]?.vehicle_id).toBe("B11622");
  });

  it("encodes line_id", async () => {
    await fetchVehicles({ lineId: "485" });
    const url = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0]?.[0];
    expect(String(url)).toContain("line_id=485");
  });
});
