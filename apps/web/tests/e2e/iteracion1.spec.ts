import { expect, test, type Page } from "@playwright/test";

/**
 * Recorrido de la iteración 1 (HU-001 a HU-009) en el navegador.
 * Los datos llevan un sufijo único para poder repetir la corrida sobre la misma base.
 */

const sufijo = Date.now().toString().slice(-7);
const ROOT_PASSWORD = process.env.E2E_ROOT_PASSWORD ?? "root-e2e";
const admin = { usuario: `admin${sufijo}`, clave: "inicial-admin" };
const cliente = {
  documento: `CC${sufijo}`,
  usuario: `cliente${sufijo}`,
  clave: "clave-cliente",
  correo: `cliente${sufijo}@example.com`,
};
let codigoVuelo = "";

function enDias(dias: number) {
  const d = new Date(Date.now() + dias * 86_400_000);
  return d.toISOString().slice(0, 10);
}

/** Avisos de error de la página (excluye el anunciador de rutas de Next.js, que también es role=alert). */
const alerta = (page: Page) => page.locator('[role="alert"]:not(#__next-route-announcer__)');

async function iniciarSesion(page: Page, usuario: string, clave: string) {
  await page.goto("/login");
  await page.getByLabel("Usuario", { exact: true }).fill(usuario);
  await page.getByLabel("Contraseña").fill(clave);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  // Espera el resultado: la redirección a la página del rol o el aviso de error.
  await Promise.race([
    page.waitForURL((url) => !url.pathname.startsWith("/login")),
    alerta(page).first().waitFor(),
  ]);
}

async function salir(page: Page) {
  await page.getByRole("button", { name: "Salir" }).click();
  await expect(page.getByRole("link", { name: "Iniciar sesión" })).toBeVisible();
}

test.describe.serial("Iteración 1", () => {
  test("HU-002 · credenciales inválidas muestran error", async ({ page }) => {
    await iniciarSesion(page, "root", "equivocada");
    await expect(alerta(page)).toContainText("Usuario o contraseña incorrectos");
    await expect(page).toHaveURL(/\/login/);
  });

  test("HU-005 · el root crea un administrador; no puede repetir el usuario", async ({ page }) => {
    await iniciarSesion(page, "root", ROOT_PASSWORD);
    await expect(page).toHaveURL(/\/admin$/);
    await expect(page.getByRole("heading", { name: "Panel de administración" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Gestión de vuelos" })).toHaveCount(0);

    await page.getByRole("link", { name: "Administradores" }).first().click();
    await page.getByLabel("Usuario").fill(admin.usuario);
    await page.getByLabel("Contraseña inicial").fill(admin.clave);
    await page.getByRole("button", { name: "Crear administrador" }).click();
    await expect(page.getByRole("status")).toContainText(`Administrador «${admin.usuario}» creado`);
    await expect(page.getByTestId("lista-administradores")).toContainText(admin.usuario);

    await page.getByLabel("Usuario").fill(admin.usuario);
    await page.getByLabel("Contraseña inicial").fill("otra");
    await page.getByRole("button", { name: "Crear administrador" }).click();
    await expect(alerta(page).first()).toContainText("Ya existe una cuenta con ese usuario");

    // RF-34: el root no entra a reservar.
    await page.goto("/reservar/FL0001");
    await expect(page).toHaveURL(/\/admin\?aviso=sin-compras/);
    await expect(alerta(page)).toContainText("no se puede reservar ni comprar");
    await salir(page);
  });

  test("HU-006 · el administrador programa un vuelo; se calcula y se publica", async ({ page }) => {
    await iniciarSesion(page, admin.usuario, admin.clave);
    await expect(page).toHaveURL(/\/admin$/);
    await page.goto("/admin/vuelos/nuevo");

    await page.getByLabel("Origen").selectOption("PEI");
    await page.getByLabel("Destino").selectOption("MAD");
    await page.getByLabel("Fecha de salida").fill(enDias(30));
    await page.getByLabel("Hora de salida").fill("20:00");
    await page.getByLabel("Tarifa primera clase (COP por persona)").fill("7000000");
    await page.getByLabel("Tarifa económica (COP por persona)").fill("2900000");
    await page.getByRole("button", { name: "Programar vuelo" }).click();

    await expect(page).toHaveURL(/\/admin\/vuelos\?programado=FL\d{4}/);
    codigoVuelo = new URL(page.url()).searchParams.get("programado")!;
    const fila = page.getByTestId(`fila-${codigoVuelo}`);
    await expect(fila).toContainText("Pereira → Madrid");
    await expect(fila).toContainText("Internacional");
    await expect(fila).toContainText(/10 h \d+ min/); // tiempo calculado, no digitado
    await expect(fila).toContainText("Editar");

    // Destinos limitados por el catálogo: desde Bucaramanga no hay internacionales.
    await page.goto("/admin/vuelos/nuevo");
    await page.getByLabel("Origen").selectOption("BGA");
    await expect(page.getByLabel("Destino").locator("option", { hasText: "Madrid" })).toHaveCount(0);
    await expect(page.getByText("Desde esta ciudad solo hay vuelos nacionales.")).toBeVisible();
  });

  test("HU-007 · el administrador edita el vuelo y se recalcula", async ({ page }) => {
    await iniciarSesion(page, admin.usuario, admin.clave);
    await page.goto(`/admin/vuelos/${codigoVuelo}`);
    await page.getByLabel("Destino").selectOption("NYC");
    await page.getByLabel("Tarifa económica (COP por persona)").fill("2500000");
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(page).toHaveURL(new RegExp(`editado=${codigoVuelo}`));
    const fila = page.getByTestId(`fila-${codigoVuelo}`);
    await expect(fila).toContainText("Pereira → New York");
    await expect(fila).toContainText(/\$\s?2\.500\.000/);
    await salir(page);
  });

  test("HU-009 · el vuelo aparece en Noticias sin iniciar sesión", async ({ page }) => {
    await page.goto("/noticias");
    const noticia = page.getByTestId("noticia").filter({ hasText: "New York" }).first();
    await expect(noticia).toContainText("Nuevo vuelo Pereira – New York");
    await expect(noticia.getByTestId("precio-noticia")).toHaveText(/\$\s?2\.500\.000/);
    await expect(noticia.getByRole("img")).toBeVisible();

    await page.goto("/");
    await expect(page.getByRole("list", { name: "Vuelos programados" })).toContainText("New York");
  });

  test("HU-008 · el visitante busca y para reservar debe identificarse", async ({ page }) => {
    await page.goto("/vuelos");
    await page.getByLabel("Origen").selectOption("PEI");
    await page.getByLabel("Destino").selectOption("NYC");
    await page.getByLabel("Pasajeros").selectOption("2");
    await page.getByRole("button", { name: "Buscar vuelos" }).click();
    await expect(page).toHaveURL(/origen=PEI&destino=NYC/);
    const resultado = page.getByTestId("resultado-vuelo").filter({ hasText: codigoVuelo });
    await expect(resultado).toBeVisible();

    await resultado.getByRole("link", { name: "Reservar" }).click();
    await expect(page).toHaveURL(/\/login\?next=/);
    await expect(page.getByText("Para reservar o comprar necesitas una cuenta de cliente.")).toBeVisible();

    // Filtros que no coinciden.
    await page.goto("/vuelos?origen=PEI&destino=NYC&precio_max=1000");
    await expect(page.getByTestId("total-resultados")).toHaveText("No encontramos vuelos con esos criterios");
  });

  test("HU-001 · registro con validaciones, documento repetido y luego inicio de sesión", async ({ page }) => {
    await page.goto("/registro");
    const llenar = async (documento: string, usuario: string) => {
      await page.getByLabel("Tipo de documento").selectOption("CEDULA");
      await page.getByLabel("Número de documento").fill(documento);
      await page.getByLabel("Nombres").fill("Laura");
      await page.getByLabel("Apellidos").fill("Gómez");
      await page.getByLabel("Fecha de nacimiento").fill("1998-06-20");
      await page.getByLabel("Lugar de nacimiento").fill("Armenia");
      await page.getByLabel("Género").selectOption("FEMENINO");
      await page.getByLabel("Dirección de facturación").fill("Calle 10 # 5-20");
      await page.getByLabel("Correo electrónico").fill(cliente.correo);
      await page.getByLabel("Usuario", { exact: true }).fill(usuario);
      await page.getByLabel("Contraseña", { exact: true }).fill(cliente.clave);
      await page.getByLabel("Confirmar contraseña").fill(cliente.clave);
      await page.getByRole("button", { name: "Crear cuenta" }).click();
    };

    await llenar("12.345-67", cliente.usuario);
    await expect(page.locator("#documento-error")).toContainText("alfanumérico");
    // Lo que el usuario ya digitó se conserva para corregir solo lo marcado.
    await expect(page.getByLabel("Género")).toHaveValue("FEMENINO");
    await expect(page.getByLabel("Nombres")).toHaveValue("Laura");

    await llenar(cliente.documento, cliente.usuario);
    await expect(page).toHaveURL(/\/login\?registrado=1/);
    await expect(page.getByRole("status")).toContainText("Tu cuenta quedó creada");

    await page.goto("/registro");
    await llenar(cliente.documento, `${cliente.usuario}b`);
    await expect(alerta(page).first()).toContainText("Ya existe una cuenta con ese documento");
    await expect(page.getByRole("link", { name: "Ir a iniciar sesión" })).toBeVisible();

    await iniciarSesion(page, cliente.usuario, cliente.clave);
    await expect(page).toHaveURL(/\/cliente$/);
    await expect(page.getByRole("heading", { name: "Hola, Laura" })).toBeVisible();
  });

  test("HU-008 · las búsquedas del cliente quedan registradas y el cliente sí entra a reservar", async ({ page }) => {
    await iniciarSesion(page, cliente.usuario, cliente.clave);
    await page.goto("/vuelos?origen=PEI&destino=NYC&pasajeros=3");
    await expect(page.getByTestId("resultado-vuelo").first()).toBeVisible();
    await page.goto("/cliente");
    await expect(page.getByTestId("busquedas-recientes")).toContainText("PEI → NYC");
    await expect(page.getByTestId("busquedas-recientes")).toContainText("3 pas.");

    await page.goto(`/reservar/${codigoVuelo}`);
    await expect(page.getByRole("heading", { name: "Pereira → New York" })).toBeVisible();
  });

  test("HU-003 · el cliente edita su perfil; un dato en blanco no se guarda", async ({ page }) => {
    await iniciarSesion(page, cliente.usuario, cliente.clave);
    await page.goto("/perfil");
    await expect(page.getByLabel("Documento", { exact: true })).toHaveValue(cliente.documento);
    await expect(page.getByLabel("Documento", { exact: true })).toBeDisabled();

    await page.getByLabel("Apellidos").fill("");
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(page.locator("#apellidos-error")).toBeVisible();

    await page.getByLabel("Apellidos").fill("Gómez Restrepo");
    await page.getByLabel("Lugar de nacimiento").fill("Pereira");
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(page.getByRole("status").first()).toContainText("Tus datos quedaron guardados");

    await salir(page);
    await iniciarSesion(page, cliente.usuario, cliente.clave);
    await page.goto("/perfil");
    await expect(page.getByLabel("Apellidos")).toHaveValue("Gómez Restrepo");
    await expect(page.getByLabel("Lugar de nacimiento")).toHaveValue("Pereira");
  });

  test("HU-004 · cambio de contraseña: solo la nueva permite ingresar", async ({ page }) => {
    await iniciarSesion(page, cliente.usuario, cliente.clave);
    await page.goto("/perfil");
    await page.getByLabel("Contraseña actual").fill("equivocada");
    await page.getByLabel("Nueva contraseña", { exact: true }).fill("nueva-clave");
    await page.getByLabel("Confirmar nueva contraseña").fill("nueva-clave");
    await page.getByRole("button", { name: "Cambiar contraseña" }).click();
    await expect(page.locator("#actual-error")).toContainText("La contraseña actual no coincide");

    await page.getByLabel("Contraseña actual").fill(cliente.clave);
    await page.getByLabel("Nueva contraseña", { exact: true }).fill("nueva-clave");
    await page.getByLabel("Confirmar nueva contraseña").fill("otra-clave");
    await page.getByRole("button", { name: "Cambiar contraseña" }).click();
    await expect(page.locator("#confirmacion-error")).toContainText("no coinciden");

    await page.getByLabel("Contraseña actual").fill(cliente.clave);
    await page.getByLabel("Nueva contraseña", { exact: true }).fill("nueva-clave");
    await page.getByLabel("Confirmar nueva contraseña").fill("nueva-clave");
    await page.getByRole("button", { name: "Cambiar contraseña" }).click();
    await expect(page.getByText("Contraseña actualizada")).toBeVisible();
    await salir(page);

    await iniciarSesion(page, cliente.usuario, cliente.clave);
    await expect(alerta(page)).toContainText("Usuario o contraseña incorrectos");
    await iniciarSesion(page, cliente.usuario, "nueva-clave");
    await expect(page).toHaveURL(/\/cliente$/);
  });

  test("HU-002 y HU-003 · el administrador completa su perfil pero sigue sin poder reservar", async ({ page }) => {
    await iniciarSesion(page, admin.usuario, admin.clave);
    await page.goto("/perfil");
    await expect(page.getByRole("heading", { name: "Completa tu registro" })).toBeVisible();
    await page.getByLabel("Número de documento").fill(`AD${sufijo}`);
    await page.getByLabel("Nombres").fill("Andrés");
    await page.getByLabel("Apellidos").fill("Ríos");
    await page.getByLabel("Fecha de nacimiento").fill("1990-01-15");
    await page.getByLabel("Lugar de nacimiento").fill("Cali");
    await page.getByLabel("Género").selectOption("MASCULINO");
    await page.getByLabel("Dirección de facturación").fill("Av. 30 de Agosto");
    await page.getByLabel("Correo electrónico").fill(`admin${sufijo}@example.com`);
    await page.getByRole("button", { name: "Completar registro" }).click();
    await expect(page.getByRole("status").first()).toContainText("Tu registro quedó completo");

    await page.goto(`/reservar/${codigoVuelo}`);
    await expect(page).toHaveURL(/\/admin\?aviso=sin-compras/);
  });
});
