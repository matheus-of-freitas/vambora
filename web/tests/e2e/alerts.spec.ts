import { expect, test } from "@playwright/test";

const STOP_ID = process.env.PLAYWRIGHT_STOP_ID ?? "3083O00030C0";

test("create, list and delete an alert on stop detail", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });

  await page.goto(`/stops/${STOP_ID}`);
  await expect(page.getByRole("heading", { name: "Alertas" })).toBeVisible({
    timeout: 20_000,
  });

  // Pick a line the stop serves and create the alert.
  const select = page.getByLabel("Linha do alerta");
  await expect(select).toBeVisible();
  const firstLine = await select.locator("option").first().getAttribute("value");
  expect(firstLine).toBeTruthy();

  const createResp = page.waitForResponse(
    (r) => r.url().includes("/alerts/rules") && r.request().method() === "POST",
    { timeout: 15_000 },
  );
  await page.getByRole("button", { name: "Criar alerta" }).click();
  const created = await createResp;
  expect(created.status()).toBe(201);

  // The new rule shows in the list with a status badge.
  const removeBtn = page.getByRole("button", {
    name: new RegExp(`Remover alerta da linha ${firstLine}`),
  });
  await expect(removeBtn).toBeVisible({ timeout: 15_000 });
  await page.screenshot({ path: "tests/e2e/alerts.png", fullPage: false });

  // Delete it.
  const delResp = page.waitForResponse(
    (r) => r.url().includes("/alerts/rules/") && r.request().method() === "DELETE",
    { timeout: 15_000 },
  );
  await removeBtn.click();
  await delResp;
  await expect(removeBtn).toBeHidden({ timeout: 15_000 });
});
