import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./auth-helper";

test.describe("E2E: Bandeja y Gestión de Leads", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("debe cargar la lista de leads y mostrar el formulario de creación", async ({ page }) => {
    await page.goto("/leads");

    await expect(page.locator("h1:has-text('Leads')")).toBeVisible();
    await expect(page.locator("text=Fichas de Evidencia")).toBeVisible();

    // Validar presencia de controles para nuevo lead
    const inputTitulo = page.locator("input[placeholder*='Título']").or(page.locator("input[type='text']").first());
    await expect(inputTitulo).toBeVisible();
  });

  test("debe permitir crear un nuevo lead y redirigir a su detalle", async ({ page }) => {
    await page.goto("/leads");

    const uniqueTitle = `E2E Lead Verificación ${Date.now()}`;
    const inputTitulo = page.locator("input[placeholder*='Título']").or(page.locator("input[type='text']").first());
    await inputTitulo.fill(uniqueTitle);

    // Enviar creación
    const btnCrear = page.locator("button:has-text('Crear')").or(page.locator("button:has-text('Guardar')")).first();
    await btnCrear.click();

    // Redirige a /leads/[id]
    await expect(page).toHaveURL(/\/leads\/\d+/, { timeout: 15000 });
    await expect(page.locator("h1", { hasText: uniqueTitle })).toBeVisible();
  });
});
