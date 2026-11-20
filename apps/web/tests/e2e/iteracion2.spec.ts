import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

/**
 * Recorrido de la iteración 2 (HU-010 a HU-018): reservar, carrito, monedero, pagar,
 * histórico y cancelar. Los vuelos y el cliente se preparan por la API.
 */

const API = "http://localhost:8000";
const ROOT_PASSWORD = process.env.E2E_ROOT_PASSWORD ?? "root-e2e";
const sufijo = Date.now().toString().slice(-7);
const cliente = { usuario: `compra${sufijo}`, clave: "clave-cliente", documento: `CP${sufijo}` };
let ida = "";
let regreso = "";

function enDias(dias: number) {
  return new Date(Date.now() + dias * 86_400_000).toISOString().slice(0, 10);
}

async function token(request: APIRequestContext, usuario: string, clave: string) {
  const r = await request.post(`${API}/auth/login`, { data: { nombre_usuario: usuario, contrasena: clave } });
  expect(r.ok()).toBeTruthy();
  return (await r.json()).access_token as string;
}

const alerta = (page: Page) => page.locator('[role="alert"]:not(#__next-route-announcer__)');

async function iniciarSesion(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuario", { exact: true }).fill(cliente.usuario);
  await page.getByLabel("Contraseña").fill(cliente.clave);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await page.waitForURL(/\/cliente/);
}

async function llenarViajero(page: Page, i: number, datos: Record<string, string>) {
  const viajero = page.getByTestId("viajero").nth(i);
  for (const [etiqueta, valor] of Object.entries(datos)) {
    if (etiqueta === "Género") await viajero.getByLabel(etiqueta).selectOption(valor);
    else await viajero.getByLabel(etiqueta, { exact: true }).fill(valor);
  }
}

const contacto = { Teléfono: "3001234567", "Contacto de emergencia": "Luz Gómez", "Teléfono del contacto": "3109876543" };

test.describe.serial("Iteración 2", () => {
  test.beforeAll(async ({ request }) => {
    const root = await token(request, "root", ROOT_PASSWORD);
    const admin = { nombre_usuario: `adm${sufijo}`, contrasena: "clave-admin-e2e" };
    await request.post(`${API}/administradores`, { data: admin, headers: { Authorization: `Bearer ${root}` } });
    const adminToken = await token(request, admin.nombre_usuario, admin.contrasena);
    const programar = async (origen: string, destino: string, dias: number) => {
      const r = await request.post(`${API}/vuelos`, {
        headers: { Authorization: `Bearer ${adminToken}` },
        data: { origen, destino, fecha_salida: enDias(dias), hora_salida: "09:15", tarifa_primera: "650000", tarifa_economica: "280000" },
      });
      expect(r.status(), await r.text()).toBe(201);
      return (await r.json()).codigo as string;
    };
    ida = await programar("PEI", "SMR", 12);
    regreso = await programar("SMR", "PEI", 16);
    const r = await request.post(`${API}/auth/registro`, {
      data: {
        documento: cliente.documento,
        tipo_documento: "CEDULA",
        nombres: "Laura",
        apellidos: "Gómez Ríos",
        fecha_nacimiento: "1992-06-20",
        lugar_nacimiento: "Pereira",
        direccion_facturacion: "Carrera 7 # 20-30",
        genero: "FEMENINO",
        correo: `compra${sufijo}@example.com`,
        nombre_usuario: cliente.usuario,
        contrasena: cliente.clave,
      },
    });
    expect(r.status(), await r.text()).toBe(201);
  });

  test("HU-012 · carrito vacío", async ({ page }) => {
    await iniciarSesion(page);
    await page.getByRole("link", { name: "Carrito" }).click();
    await expect(page.getByText("Tu carrito está vacío.")).toBeVisible();
  });

  test("HU-010 · reserva ida y vuelta para dos viajeros; el menor no viaja solo", async ({ page }) => {
    await iniciarSesion(page);
    await page.goto(`/reservar/${ida}`);
    // El primer viajero viene con los datos del perfil.
    await expect(page.getByTestId("viajero").first().getByLabel("Nombres")).toHaveValue("Laura");
    await page.getByLabel("Trayecto").selectOption("IDA_Y_VUELTA");
    await page.getByLabel("Vuelo de regreso").selectOption(regreso);
    await page.getByLabel("Viajeros", { exact: true }).selectOption("2");
    await expect(page.getByTestId("total-reserva")).toContainText("1.120.000");

    // Solo un menor: rechazado.
    await llenarViajero(page, 0, { "Fecha de nacimiento": enDias(-8 * 365), ...contacto });
    await llenarViajero(page, 1, {
      Documento: `TI${sufijo}`,
      Nombres: "Tomás",
      Apellidos: "Gómez Ríos",
      "Fecha de nacimiento": enDias(-6 * 365),
      Género: "MASCULINO",
      Correo: `tomas${sufijo}@example.com`,
      ...contacto,
    });
    await page.getByRole("button", { name: "Agregar al carrito (reservar)" }).click();
    await expect(alerta(page).first()).toContainText("menor");

    await llenarViajero(page, 0, { "Fecha de nacimiento": "1992-06-20" });
    await page.getByRole("button", { name: "Agregar al carrito (reservar)" }).click();
    await page.waitForURL(/\/cliente\/reservas\/[A-Z0-9]{6}\?nueva=1/);
    await expect(page.getByText("Reserva creada y agregada al carrito")).toBeVisible();
    await expect(page.getByTestId("tiquete")).toHaveCount(4);
    await expect(page.getByTestId("estado-reserva")).toHaveText("Reservada");
  });

  test("HU-012 y HU-013 · saldo insuficiente; se recarga el monedero y se paga", async ({ page }) => {
    await iniciarSesion(page);
    await page.goto("/cliente/carrito");
    await expect(page.getByTestId("reserva")).toHaveCount(1);
    await expect(page.getByTestId("total-carrito")).toContainText("1.120.000");
    await page.getByRole("link", { name: "Pagar todo" }).click();
    await expect(alerta(page)).toContainText("Tu saldo no alcanza");
    await page.getByRole("button", { name: "Intentar pagar" }).click();
    await expect(alerta(page).last()).toContainText("Saldo insuficiente: tienes $0 y se necesitan $1.120.000");

    await page.goto("/cliente/monedero");
    await page.getByLabel("Nuevo saldo").fill("2000000");
    await page.getByRole("button", { name: "Actualizar saldo" }).click();
    await expect(page.getByTestId("saldo")).toContainText("2.000.000");
    await expect(page.getByTestId("movimientos")).toContainText("Ajuste manual");

    await page.getByLabel("Titular").fill("LAURA GOMEZ");
    await page.getByLabel("Número de la tarjeta").fill("4111 1111 1111 1111");
    await page.getByLabel("Vence (MM/AA)").fill("10/31");
    await page.getByRole("button", { name: "Agregar tarjeta" }).click();
    await expect(page.getByTestId("tarjetas")).toContainText("•••• 1111");

    await page.goto("/cliente/pago");
    await expect(page.getByTestId("total-pago")).toContainText("1.120.000");
    await page.getByRole("button", { name: "Pagar con el monedero" }).click();
    await page.waitForURL(/comprada=1/);
    await expect(page.getByText("Compra realizada")).toBeVisible();
    await expect(page.getByTestId("estado-reserva")).toHaveText("Pagada");

    await page.goto("/cliente/monedero");
    await expect(page.getByTestId("saldo")).toContainText("880.000");
    await expect(page.getByTestId("movimientos")).toContainText("Compra de tiquetes");
  });

  test("HU-016 · reserva sencilla que se cancela antes de pagar", async ({ page }) => {
    await iniciarSesion(page);
    await page.goto(`/reservar/${ida}`);
    await page.getByRole("radio", { name: /Primera/ }).click();
    await llenarViajero(page, 0, { Documento: `OT${sufijo}`, Nombres: "Mario", Correo: `mario${sufijo}@example.com`, ...contacto });
    await page.getByRole("button", { name: "Agregar al carrito (reservar)" }).click();
    await page.waitForURL(/nueva=1/);
    await page.getByLabel(/se liberan las sillas/).check();
    await page.getByRole("button", { name: "Cancelar reserva" }).click();
    await page.waitForURL(/cancelada=1/);
    await expect(page.getByText("Reserva cancelada")).toBeVisible();
  });

  test("HU-017 y HU-015 · histórico y cancelación de la compra con reembolso", async ({ page }) => {
    await iniciarSesion(page);
    await page.getByRole("link", { name: "Mis reservas" }).click();
    await expect(page.getByTestId("reserva")).toHaveCount(2);
    await expect(page.getByTestId("estado-reserva")).toHaveText(["Cancelada", "Pagada"]);
    await page.getByRole("link", { name: "Ver detalle" }).last().click();
    await page.getByLabel(/vuelve completo a mi monedero/).check();
    await page.getByRole("button", { name: "Cancelar compra" }).click();
    await page.waitForURL(/cancelada=1/);
    await expect(page.getByText(/Devolvimos .*1\.120\.000/)).toBeVisible();
    await page.goto("/cliente/monedero");
    await expect(page.getByTestId("saldo")).toContainText("2.000.000");
  });
});
