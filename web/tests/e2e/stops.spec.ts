import { expect, test } from "@playwright/test";

test("stop detail page loads, can be favorited, persists, appears in /favorites", async ({
  page,
}) => {
  await page.goto("/stops/1002O00010C0");
  await page.waitForResponse(
    (r) =>
      r.request().resourceType() === "fetch" &&
      r.url().includes("/stops/1002O00010C0") &&
      r.status() === 200,
    { timeout: 15_000 },
  );
  await expect(page.locator("h1")).toContainText("AquaRio");
  await expect(page.locator("body")).toContainText("1002O00010C0");

  // Star the stop.
  const star = page.getByLabel("Adicionar aos favoritos");
  await expect(star).toBeVisible();
  await star.click();
  await expect(page.getByLabel("Remover dos favoritos")).toBeVisible();

  // Reload — IDB persists.
  await page.reload();
  await expect(page.getByLabel("Remover dos favoritos")).toBeVisible();

  // Favorites page lists the stop.
  await page.goto("/favorites");
  await expect(page.getByText("AquaRio")).toBeVisible();

  // Unstar — wait for the visual state to flip before navigating, otherwise
  // the IDB write can race with the next page load.
  await page.goto("/stops/1002O00010C0");
  await page.getByLabel("Remover dos favoritos").click();
  await expect(page.getByLabel("Adicionar aos favoritos")).toBeVisible();
  await page.goto("/favorites");
  await expect(page.getByText("Nenhum favorito ainda")).toBeVisible();
});

test("unknown stop renders not-found state", async ({ page }) => {
  await page.goto("/stops/THIS_STOP_DOES_NOT_EXIST");
  await expect(page.locator("body")).toContainText("Parada não encontrada");
});
