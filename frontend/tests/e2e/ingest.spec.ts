import { test, expect } from "@playwright/test";

test.describe("E2E: Ingesta y Reporte de Calidad (/ingest)", () => {
  test("debe cargar la vista de ingesta y mostrar el contenedor de reporte de calidad", async ({ page }) => {
    await page.goto("/ingest");

    await expect(page.locator("h1:has-text('Ingesta y calidad')")).toBeVisible();
    await expect(page.locator("text=Ejecutar carga")).toBeVisible();
    await expect(page.locator("button:has-text('Ejecutar ingesta')")).toBeVisible();

    // Validar checkbox de snapshot local
    const checkboxSnapshot = page.locator("input[type='checkbox']");
    await expect(checkboxSnapshot).toBeVisible();
    await expect(checkboxSnapshot).toBeChecked();
  });
});
