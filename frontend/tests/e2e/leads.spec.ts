import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./auth-helper";

test.describe("E2E: Bandeja y Gestión de Leads", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("debe cargar la lista de leads con el acceso a crear", async ({ page }) => {
    await page.goto("/leads");

    await expect(page.locator("h1:has-text('Leads')")).toBeVisible();
    await expect(page.locator("text=Fichas de Evidencia")).toBeVisible();

    // La creación vive en el asistente, enlazado desde la lista.
    await expect(page.locator("a[href='/leads/new']").first()).toBeVisible();
  });

  test("debe crear un nuevo lead a través del asistente", async ({ page }) => {
    await page.goto("/leads");
    await page.locator("a[href='/leads/new']").first().click();
    await expect(page).toHaveURL(/\/leads\/new/);

    // El ejemplo rellena un título válido y la modalidad.
    await page.click("button:has-text('Usar ejemplo')");

    const [resp] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes("/api/cases") && r.request().method() === "POST",
        { timeout: 15000 }
      ),
      page.click("button:has-text('Crear lead')"),
    ]);
    expect(resp.ok()).toBeTruthy();

    // El asistente avanza al paso 2 "Evidencia" en el mismo lugar.
    await expect(page.locator("h2:has-text('Evidencia')")).toBeVisible({ timeout: 15000 });
  });
});
