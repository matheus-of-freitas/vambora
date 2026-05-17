import { expect, test } from "@playwright/test";

const grabMap = () => {
  const map = (window as unknown as { __VAMBORA_MAP__?: maplibregl.Map }).__VAMBORA_MAP__;
  if (!map) throw new Error("__VAMBORA_MAP__ not exposed (production build?)");
  return map;
};

test("clicking a vehicle shows popup with vehicle id and line link", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  await page.waitForResponse((r) => r.url().includes("/vehicles") && r.status() === 200, {
    timeout: 15_000,
  });
  // Wait for the dev-mode map handle to be available.
  await page.waitForFunction(
    () => {
      const map = (window as unknown as { __VAMBORA_MAP__?: maplibregl.Map }).__VAMBORA_MAP__;
      if (!map) return false;
      const src = map.getSource("vehicles") as maplibregl.GeoJSONSource | undefined;
      return src !== undefined;
    },
    { timeout: 10_000 },
  );

  // Pick a real vehicle the source actually contains.
  const target = await page.evaluate(() => {
    type Feature = GeoJSON.Feature<GeoJSON.Point, { vehicle_id: string; line_id: string }>;
    const map = (window as unknown as { __VAMBORA_MAP__?: maplibregl.Map }).__VAMBORA_MAP__;
    if (!map) return null;
    const src = map.getSource("vehicles") as maplibregl.GeoJSONSource & {
      _data?: GeoJSON.FeatureCollection<GeoJSON.Point>;
    };
    const f = (src._data?.features?.[0] ?? null) as Feature | null;
    if (!f) return null;
    const lng = f.geometry.coordinates[0];
    const lat = f.geometry.coordinates[1];
    if (lng === undefined || lat === undefined) return null;
    return {
      vehicle_id: f.properties.vehicle_id,
      line_id: f.properties.line_id,
      lng,
      lat,
    };
  });
  expect(target).not.toBeNull();
  if (!target) return;

  // Center on the vehicle and zoom so the dot is unambiguous.
  await page.evaluate((t) => {
    const map = (window as unknown as { __VAMBORA_MAP__?: maplibregl.Map }).__VAMBORA_MAP__;
    if (!map) throw new Error("no map");
    map.jumpTo({ center: [t.lng, t.lat], zoom: 17 });
  }, target);
  await page.waitForTimeout(400);

  // Project to screen pixels and click there.
  const point = await page.evaluate((t) => {
    const map = (window as unknown as { __VAMBORA_MAP__?: maplibregl.Map }).__VAMBORA_MAP__;
    if (!map) throw new Error("no map");
    const p = map.project([t.lng, t.lat]);
    const r = map.getCanvas().getBoundingClientRect();
    return { x: r.left + p.x, y: r.top + p.y };
  }, target);
  await page.mouse.click(point.x, point.y);

  await expect(page.locator(".maplibregl-popup")).toContainText(target.vehicle_id);
  if (target.line_id) {
    await expect(page.locator(".maplibregl-popup a")).toContainText("Ver linha");
  }
});

// keep grabMap exported helper unused-but-defined to silence "noUnusedLocals" — ignore via void
void grabMap;
