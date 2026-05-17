import { expect, test } from "@playwright/test";

// A stop on busy Rio lines; overridable if live data shifts.
const STOP_ID = process.env.PLAYWRIGHT_STOP_ID ?? "3083O00030C0";

test("stop detail shows live ETAs with a realtime badge", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });

  const predResp = page.waitForResponse(
    (r) => r.url().includes(`/stops/${STOP_ID}/predictions`) && r.status() === 200,
    { timeout: 30_000 },
  );

  await page.goto(`/stops/${STOP_ID}`);

  const predictions = await (await predResp).json();
  expect(Array.isArray(predictions)).toBe(true);

  await expect(page.locator("body")).toContainText("Chegando agora");
  await expect(page.locator("body")).toContainText("Próximas saídas");

  if (predictions.length > 0) {
    await expect(page.getByText("Ao vivo")).toBeVisible();
    // At least one predicted ETA row like "3 min".
    await expect(page.locator("body")).toContainText(/\d+\s*min/);
  }

  await page.waitForTimeout(1200);
  await page.screenshot({ path: "tests/e2e/predictions.png", fullPage: false });
});
