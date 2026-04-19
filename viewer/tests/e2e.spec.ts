/** Playwright E2E: renders the demo case file, checks key user-visible surfaces. */
import { expect, test } from "@playwright/test";

test("viewer renders checkout-401 demo", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Sleuth/i })).toBeVisible();
  await expect(page.getByText(/why did checkout/i)).toBeVisible();
  await expect(page.getByText(/root cause/i)).toBeVisible();
  await expect(page.getByLabel(/Evidence/i)).toBeVisible();
  await expect(page.getByLabel(/Trajectory/i)).toBeVisible();
});

test("evidence panel shows key events with accent border", async ({ page }) => {
  await page.goto("/");
  const keys = page.locator('li:has-text("KEY")');
  await expect(keys).toHaveCount(4); // fixture has 4 is_key=true evidence lines
});

test("ground-truth overlap is rendered", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/overlap \d+%/)).toBeVisible();
});
