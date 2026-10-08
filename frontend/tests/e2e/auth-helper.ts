import { type Page, expect } from "@playwright/test";

export const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@vertexdc.com";
export const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "Vtx-Dev-EvidentIA#2026!7x";

export async function loginAsAdmin(page: Page): Promise<void> {
  await page.goto("/login");
  await page.fill("input[type='email']", ADMIN_EMAIL);
  await page.fill("input[type='password']", ADMIN_PASSWORD);
  await page.click("button:has-text('Acceder a EvidentIA')");
  await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
}
