import { expect, test } from "@playwright/test";

// Full offline document/route loading depends on the production service
// worker (precaches the app shell); `pnpm dev` has no SW, so we don't drive
// cross-route offline navigation here. Instead we prove: (1) the bundle
// downloads and persists via the UI, and (2) what persisted in IndexedDB is
// the correct data the offline fallback consumes. The fallback transform
// itself is unit-tested (tests/unit/line-shape-offline.test.ts).
test("download offline bundle and persist correct data", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });

  await page.goto("/");
  await page.getByRole("link", { name: "Offline" }).click();
  await expect(page.locator("h1")).toContainText("Uso offline");

  const latestResp = page.waitForResponse(
    (r) => r.url().includes("/snapshots/latest") && r.status() === 200,
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: /Baixar dados para uso offline/ }).click();
  await latestResp;

  await expect(page.getByText("Salvo no dispositivo")).toBeVisible({ timeout: 30_000 });
  await expect(page.locator("body")).toContainText(/\d+ linhas · \d+ paradas/);
  await page.screenshot({ path: "tests/e2e/offline-bundle.png", fullPage: false });

  // The persisted bundle is the real data the offline fallback reads.
  const probe = await page.evaluate(async () => {
    const open = indexedDB.open("vambora-bundle", 1);
    const dbi: IDBDatabase = await new Promise((res, rej) => {
      open.onsuccess = () => res(open.result);
      open.onerror = () => rej(open.error);
    });
    const bundle = await new Promise<{
      meta: { route_count: number; stop_count: number };
      line_shapes: Record<string, [number, number][][]>;
      stop_lines: Record<string, string[]>;
    }>((res, rej) => {
      const req = dbi.transaction("bundle").objectStore("bundle").get("current");
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
    return {
      routes: bundle.meta.route_count,
      stops: bundle.meta.stop_count,
      has485: Array.isArray(bundle.line_shapes["485"]),
      pts485: bundle.line_shapes["485"]?.[0]?.length ?? 0,
      stopLineStops: Object.keys(bundle.stop_lines).length,
      sampleStopLines: bundle.stop_lines["3083O00030C0"] ?? [],
    };
  });

  expect(probe.routes).toBeGreaterThan(100);
  expect(probe.stops).toBeGreaterThan(1000);
  expect(probe.has485).toBe(true);
  expect(probe.pts485).toBeGreaterThan(1);
  expect(probe.stopLineStops).toBeGreaterThan(1000);
  expect(probe.sampleStopLines).toContain("639");
});
