import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial" });

test("star a line, persist across reload, see in favorites, navigate, unstar", async ({
  page,
  context,
}) => {
  // Each test gets a fresh storage state from Playwright by default; clear IDB
  // explicitly to be safe.
  await context.clearCookies();
  await page.goto("/lines/485");
  await page.waitForResponse((r) => r.url().includes("/lines/485/realtime") && r.status() === 200, {
    timeout: 15_000,
  });

  const star = page.getByLabel("Adicionar aos favoritos");
  await expect(star).toBeVisible();
  await star.click();
  // Aria-label flips to "Remover".
  const filledStar = page.getByLabel("Remover dos favoritos");
  await expect(filledStar).toBeVisible();

  // Reload — state lives in IDB so the star should still be filled.
  await page.reload();
  await expect(page.getByLabel("Remover dos favoritos")).toBeVisible();

  // /favorites should list 485.
  await page.goto("/favorites");
  await expect(page.getByTestId("fav-line-485")).toBeVisible();
  await expect(page.getByTestId("fav-line-485")).toContainText("485");

  // Click the favorite → /lines/485.
  await page.getByTestId("fav-line-485").click();
  await page.waitForURL("**/lines/485");

  // Unstar — toggles back to "Adicionar".
  await page.getByLabel("Remover dos favoritos").click();
  await expect(page.getByLabel("Adicionar aos favoritos")).toBeVisible();

  // /favorites should now show empty state.
  await page.goto("/favorites");
  await expect(page.getByText("Nenhum favorito ainda")).toBeVisible();
});
