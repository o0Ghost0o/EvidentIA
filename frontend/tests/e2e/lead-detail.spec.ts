import { test, expect } from "@playwright/test";

test.describe("E2E: Detalle de Ficha y Evidencias (/leads/:id)", () => {
  test("debe cargar la ficha del lead, árbol jerárquico y panel de notas", async ({ page }) => {
    // Primero crear o navegar a un lead existente
    await page.goto("/leads");

    const uniqueTitle = `E2E Lead Detalle ${Date.now()}`;
    const inputTitulo = page.locator("input[placeholder*='Título']").or(page.locator("input[type='text']").first());
    await inputTitulo.fill(uniqueTitle);

    const btnCrear = page.locator("button:has-text('Crear')").or(page.locator("button:has-text('Guardar')")).first();
    await btnCrear.click();

    await expect(page).toHaveURL(/\/leads\/\d+/, { timeout: 15000 });

    // Validar secciones críticas de la ficha
    await expect(page.locator("h1", { hasText: uniqueTitle })).toBeVisible();
    await expect(page.locator("text=Árbol Jerárquico de Evidencia")).toBeVisible();
    await expect(page.locator("text=Revisión humana y trazabilidad").or(page.locator("text=Borrador de Síntesis")).first()).toBeVisible();

    // Validar presencia del botón de generar borrador/brief
    const btnBrief = page.locator("button:has-text('Generar borrador de ficha')").or(page.locator("button:has-text('Generar')")).first();
    await expect(btnBrief).toBeVisible();
  });
});
