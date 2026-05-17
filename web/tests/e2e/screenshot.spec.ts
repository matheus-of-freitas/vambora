import { test } from "@playwright/test";

test("capture home screenshot", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  await page.waitForResponse((resp) => resp.url().includes("/vehicles") && resp.status() === 200, {
    timeout: 15_000,
  });
  // Let MapLibre paint and the vehicle layer render.
  await page.waitForTimeout(2000);
  await page.screenshot({ path: "tests/e2e/home.png", fullPage: false });
});
