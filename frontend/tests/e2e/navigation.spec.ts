import { test, expect } from "@playwright/test";

test.describe("E2E: Navegación Global y Header", () => {
  test("debe cargar la página principal (Bandeja de temas) y mostrar el header", async ({ page }) => {
    await page.goto("/");

    // Validar marca y enlaces principales del navbar
    await expect(page.locator("nav")).toBeVisible();
    await expect(page.locator("nav a:has-text('EvidentIA')")).toBeVisible();
    await expect(page.locator("nav a:has-text('Bandeja')")).toBeVisible();
    await expect(page.locator("nav a:has-text('Leads')")).toBeVisible();
    await expect(page.locator("nav a:has-text('Ingesta')")).toBeVisible();

    // Validar encabezado principal de la bandeja
    await expect(page.locator("h1:has-text('Bandeja de temas')")).toBeVisible();
  });

  test("debe navegar entre Bandeja, Leads e Ingesta a través del menú", async ({ page }) => {
    await page.goto("/");

    // Clic en Leads
    await page.click("nav a:has-text('Leads')");
    await expect(page).toHaveURL(/\/leads/);
    await expect(page.locator("h1:has-text('Leads')")).toBeVisible();

    // Clic en Ingesta
    await page.click("nav a:has-text('Ingesta')");
    await expect(page).toHaveURL(/\/ingest/);
    await expect(page.locator("h1:has-text('Ingesta y calidad')")).toBeVisible();

    // Retornar a Bandeja
    await page.click("nav a:has-text('Bandeja')");
    await expect(page).toHaveURL(/\//);
    await expect(page.locator("h1:has-text('Bandeja de temas')")).toBeVisible();
  });
});
