import { expect, test } from "@playwright/test";

test("typing a line into search navigates to /lines/{shortName}", async ({ page }) => {
  await page.goto("/");
  await page.waitForResponse((r) => r.url().includes("/vehicles") && r.status() === 200, {
    timeout: 15_000,
  });
  const search = page.getByLabel("Número ou código da linha");
  await search.fill("485");
  await search.press("Enter");
  await page.waitForURL("**/lines/485");
  await expect(page.locator("h1")).toContainText("485");
  await expect(page.locator("body")).toContainText("Fundão");
});

test("empty search does not navigate", async ({ page }) => {
  await page.goto("/");
  const search = page.getByLabel("Número ou código da linha");
  await search.press("Enter");
  // Still on home; vehicles count chip should be visible.
  await expect(page.locator("h1")).toContainText("Vambora");
});
