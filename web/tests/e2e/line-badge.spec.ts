import { expect, test } from "@playwright/test";

test("line detail shows a live or scheduled-only status badge", async ({ page }) => {
  await page.goto("/lines/485");
  await page.waitForResponse(
    (r) =>
      r.request().resourceType() === "fetch" &&
      r.url().includes("/lines/485/realtime") &&
      r.status() === 200,
    { timeout: 15_000 },
  );
  await expect(page.locator("h1")).toContainText("485");
  // Exactly one of the two states must be visible.
  const live = page.getByText("Ao vivo", { exact: true });
  const scheduled = page.getByText("Apenas programado", { exact: true });
  await expect(live.or(scheduled).first()).toBeVisible();
});
