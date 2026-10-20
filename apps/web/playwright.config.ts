import { defineConfig, devices } from "@playwright/test";

/**
 * Pruebas de extremo a extremo de la iteración 1 contra la API y la web reales.
 *
 * Requiere un PostgreSQL disponible en E2E_DATABASE_URL (por defecto la base `tiquetes_e2e`
 * en localhost). La API aplica las migraciones al arrancar y el root toma ROOT_PASSWORD.
 */
const API_PORT = 8000;
const WEB_PORT = 3000;
const DB = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg://postgres:postgres@localhost:5432/tiquetes_e2e";
export const ROOT_PASSWORD = process.env.E2E_ROOT_PASSWORD ?? "root-e2e";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    locale: "es-CO",
    timezoneId: "America/Bogota",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run alembic upgrade head && uv run uvicorn app.main:app --port ${API_PORT}`,
      cwd: "../api",
      url: `http://localhost:${API_PORT}/salud`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        DATABASE_URL: DB,
        ROOT_PASSWORD,
        JWT_SECRET: "secreto-e2e-con-longitud-suficiente-para-hs256",
        CORS_ORIGENES: `http://localhost:${WEB_PORT}`,
      },
    },
    {
      command: `pnpm start`,
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { API_URL: `http://localhost:${API_PORT}`, COOKIE_INSEGURA: "1", PORT: String(WEB_PORT) },
    },
  ],
});
