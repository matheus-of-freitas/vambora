import { expect, test } from "@playwright/test";

test("planner plans a trip and renders an itinerary", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });

  const responsePromise = page.waitForResponse(
    (resp) => resp.url().includes("/trips/plan") && resp.status() === 200,
    { timeout: 30_000 },
  );

  await page.goto("/planner");
  await expect(page.locator("h1")).toContainText("Planejar viagem");

  // Defaults are Copacabana -> Centro (distinct), so just submit.
  await page.getByRole("button", { name: "Planejar" }).click();

  const response = await responsePromise;
  const itineraries = await response.json();
  expect(Array.isArray(itineraries)).toBe(true);
  expect(itineraries.length).toBeGreaterThan(0);

  // The result panel renders at least one itinerary (a duration selector
  // button like "44 min" plus the start -> end time row with an arrow).
  await expect(page.locator("body")).toContainText(/\d+\s*(min|h)/, { timeout: 15_000 });
  await expect(page.locator("body")).toContainText("→");

  await page.waitForTimeout(1500); // let MapLibre paint the route
  await page.screenshot({ path: "tests/e2e/planner.png", fullPage: false });
});
