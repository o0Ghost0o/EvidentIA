import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@vertexdc.com";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "Vtx-Dev-EvidentIA#2026!7x";

test.describe("E2E: Autenticación Obligatoria y Navegación", () => {
  test("visitar la raíz sin sesión debe redirigir inmediatamente a /login", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator("h1:has-text('EvidentIA')")).toBeVisible();
    await expect(page.locator("text=Iniciar Sesión")).toBeVisible();
    await expect(page.locator("input[type='password']")).toHaveValue("");
  });

  test("debe permitir iniciar sesión con credenciales válidas y acceder a la bandeja", async ({ page }) => {
    await page.goto("/login");

    // Llenar campos limpios
    await page.fill("input[type='email']", ADMIN_EMAIL);
    await page.fill("input[type='password']", ADMIN_PASSWORD);

    // Enviar
    await page.click("button:has-text('Acceder a EvidentIA')");

    // Redirige al dashboard
    await expect(page).toHaveURL(/\//, { timeout: 15000 });
    await expect(page.locator("h1:has-text('Bandeja de temas')")).toBeVisible();

    // Validar presencia del usuario en header
    await expect(page.locator(`text=${ADMIN_EMAIL}`)).toBeVisible();
    await expect(page.locator("button:has-text('Cerrar Sesión')")).toBeVisible();
  });

  test("debe permitir cerrar sesión y bloquear el acceso nuevamente", async ({ page }) => {
    // 1. Iniciar sesión
    await page.goto("/login");
    await page.fill("input[type='email']", ADMIN_EMAIL);
    await page.fill("input[type='password']", ADMIN_PASSWORD);
    await page.click("button:has-text('Acceder a EvidentIA')");
    await expect(page).toHaveURL(/\//, { timeout: 15000 });

    // 2. Cerrar sesión
    await page.click("button:has-text('Cerrar Sesión')");
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });

    // 3. Intentar volver a /leads debe redirigir a /login
    await page.goto("/leads");
    await expect(page).toHaveURL(/\/login/);
  });
});
