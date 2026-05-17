import { expect, test } from "@playwright/test";

test("manifest is reachable and references the expected fields", async ({ request }) => {
  const r = await request.get("/manifest.webmanifest");
  expect(r.status()).toBe(200);
  const manifest = (await r.json()) as Record<string, unknown>;
  expect(manifest.name).toBe("Vambora");
  expect(manifest.start_url).toBe("/");
  expect(manifest.display).toBe("standalone");
  expect(manifest.theme_color).toBe("#fbbf24");
  expect(Array.isArray(manifest.icons)).toBe(true);
});

test("layout advertises the manifest and theme-color", async ({ page }) => {
  await page.goto("/");
  const manifestHref = await page.locator('link[rel="manifest"]').first().getAttribute("href");
  expect(manifestHref).toContain("manifest");
  const themeColor = await page.locator('meta[name="theme-color"]').first().getAttribute("content");
  expect(themeColor).toBe("#fbbf24");
});

test("sw.js is a valid, installable service worker", async ({ page }) => {
  // The app only auto-registers the SW in production builds (dev Next.js
  // serves drifting hashed asset URLs). Here we register it explicitly to
  // verify sw.js itself installs and activates — the prod-only gating is a
  // separate concern, asserted by reading the registrar component.
  await page.goto("/");
  const state = await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    await navigator.serviceWorker.ready;
    const worker = reg.active ?? reg.waiting ?? reg.installing;
    if (!worker) return null;
    if (worker.state === "activated") return "activated";
    return await new Promise<string>((resolve) => {
      worker.addEventListener("statechange", () => {
        if (worker.state === "activated") resolve("activated");
      });
      // Safety: resolve with whatever state we end on after a short grace.
      setTimeout(() => resolve(worker.state), 5000);
    });
  });
  expect(state).toBe("activated");
});

test("offline page renders the pt-BR fallback", async ({ page }) => {
  await page.goto("/offline");
  await expect(page.locator("h1")).toContainText("Sem conexão");
  await expect(page.locator("body")).toContainText("favoritos");
});
