import { expect, test } from "@playwright/test";

test("stop detail shows scheduled arrivals with relative time", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/stops/1002O00010C0");
  await page.waitForResponse(
    (r) => r.url().includes("/stops/1002O00010C0/arrivals") && r.status() === 200,
    { timeout: 15_000 },
  );
  await expect(page.getByText("Próximas saídas")).toBeVisible();
  const bodyText = (await page.locator("body").textContent()) ?? "";
  expect(bodyText).toMatch(/\d{1,2}:\d{2}/);
  // Either "agora" or "em N min" should appear when arrivals are within the
  // next hour (true with the GTFS_DATE_OVERRIDE projection at AquaRio).
  expect(bodyText).toMatch(/(agora|em \d+ min)/);
  await page.waitForTimeout(500);
  await page.screenshot({ path: "tests/e2e/arrivals.png", fullPage: false });
});

test("clicking an arrival navigates to its line page", async ({ page }) => {
  await page.goto("/stops/1002O00010C0");
  await page.waitForResponse(
    (r) => r.url().includes("/stops/1002O00010C0/arrivals") && r.status() === 200,
    { timeout: 15_000 },
  );
  // First arrival is wrapped in a Link to /lines/{shortName}.
  const firstArrival = page.locator('a[href^="/lines/"]').first();
  await expect(firstArrival).toBeVisible();
  const href = await firstArrival.getAttribute("href");
  expect(href).toMatch(/^\/lines\/.+/);
  await firstArrival.click();
  await page.waitForURL(/\/lines\/.+/);
  await expect(page.locator("h1")).toBeVisible();
});
