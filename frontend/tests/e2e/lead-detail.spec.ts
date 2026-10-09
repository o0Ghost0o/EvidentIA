import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./auth-helper";

const EXAMPLE_TITLE = "Alza en tarifas eléctricas";

test.describe("E2E: Ficha de solo lectura (/leads/:id)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("abre la ficha de solo lectura reutilizando los pasos del asistente", async ({ page }) => {
    // Crear un lead con el asistente (el ejemplo rellena un título válido + modalidad).
    await page.goto("/leads/new");
    await page.click("button:has-text('Usar ejemplo')");

    const [resp] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes("/api/cases") && r.request().method() === "POST",
        { timeout: 15000 }
      ),
      page.click("button:has-text('Crear lead')"),
    ]);
    const { id } = (await resp.json()) as { id: number };
    expect(id).toBeGreaterThan(0);

    // Abrir el detalle: debe renderizar la ficha en el diseño nuevo.
    await page.goto(`/leads/${id}`);
    await expect(page.locator("h1", { hasText: EXAMPLE_TITLE })).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Ficha completa · 6/6 pasos")).toBeVisible();

    // Los seis pasos reutilizados están presentes como secciones.
    await expect(page.locator("h2:has-text('Evidencia')")).toBeVisible();
    await expect(page.locator("h2:has-text('Ficha')")).toBeVisible();
    await expect(page.locator("h2:has-text('Revisión')")).toBeVisible();

    // Es de solo lectura: los controles de edición del asistente no aparecen.
    await expect(page.locator("button:has-text('+ Vincular fuentes')")).toHaveCount(0);
    await expect(page.locator("button:has-text('Generar borrador')")).toHaveCount(0);
    await expect(page.locator("button:has-text('Guardar decisión')")).toHaveCount(0);
    await expect(page.locator("button:has-text('Continuar')")).toHaveCount(0);
  });

  test("permite abrir una ficha desde la lista", async ({ page }) => {
    // Sembrar un lead vía el asistente.
    await page.goto("/leads/new");
    await page.click("button:has-text('Usar ejemplo')");
    await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes("/api/cases") && r.request().method() === "POST",
        { timeout: 15000 }
      ),
      page.click("button:has-text('Crear lead')"),
    ]);

    // Desde la lista, un clic en la fila abre el detalle.
    await page.goto("/leads");
    const row = page.locator("[role='link']", { hasText: EXAMPLE_TITLE }).first();
    await expect(row).toBeVisible({ timeout: 15000 });
    await row.click();
    await expect(page).toHaveURL(/\/leads\/\d+/, { timeout: 15000 });
    await expect(page.locator("h1", { hasText: EXAMPLE_TITLE })).toBeVisible();
  });
});
