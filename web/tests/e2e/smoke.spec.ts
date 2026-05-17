import { expect, test } from "@playwright/test";

test("home renders Vambora branding and fetches vehicles", async ({ page }) => {
  const responsePromise = page.waitForResponse(
    (resp) => resp.url().includes("/vehicles") && resp.status() === 200,
    { timeout: 15_000 },
  );

  await page.goto("/");

  await expect(page.locator("h1")).toContainText("Vambora");
  await expect(page.locator("body")).toContainText("Seu transporte público no Rio em tempo real");

  const response = await responsePromise;
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  expect(data.length).toBeGreaterThan(0);

  // Wait for the status bar to render the vehicle count.
  const status = page.locator("aside, div", { hasText: /\d+ ônibus/ }).first();
  await expect(status).toBeVisible({ timeout: 15_000 });
});
