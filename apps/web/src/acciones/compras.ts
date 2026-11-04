"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { api, ApiError, estadoDeError } from "@/lib/api";
import { exigirSesion } from "@/lib/sesion";
import type { EstadoFormulario, Monedero, Pago, ReservaDetalle } from "@/lib/tipos";
import { CAMPOS_VIAJERO, camposDelFormulario } from "@/lib/viajero";

const texto = (form: FormData, campo: string) => String(form.get(campo) ?? "").trim();

/** HU-010 y HU-011: crea la reserva; con «Comprar ahora» pasa directo a la confirmación del pago. */
export async function reservar(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("CLIENTE");
  const cantidad = Math.min(5, Math.max(1, Number(texto(form, "cantidad")) || 1));
  const valores: Record<string, string> = {
    cantidad: String(cantidad),
    clase: texto(form, "clase"),
    trayecto: texto(form, "trayecto"),
    regreso: texto(form, "regreso"),
  };
  const pasajeros = Array.from({ length: cantidad }, (_, i) => {
    const p: Record<string, string> = {};
    for (const c of CAMPOS_VIAJERO) {
      p[c] = texto(form, `p${i}_${c}`);
      valores[`p${i}_${c}`] = p[c];
    }
    return p;
  });
  const vuelo = texto(form, "vuelo");
  const regreso = valores.trayecto === "IDA_Y_VUELTA" ? valores.regreso : "";
  if (valores.trayecto === "IDA_Y_VUELTA" && !regreso) {
    return { ok: false, mensaje: "Elige el vuelo de regreso.", campos: { regreso: "Elige el vuelo de regreso." }, valores };
  }

  let reserva: ReservaDetalle;
  try {
    reserva = await api<ReservaDetalle>("/reservas", {
      metodo: "POST",
      token: sesion.token,
      cuerpo: { vuelo_codigo: vuelo, vuelo_regreso_codigo: regreso || null, clase: valores.clase, pasajeros },
    });
  } catch (e) {
    if (e instanceof ApiError) {
      return { ok: false, mensaje: e.message, campos: camposDelFormulario(e.campos), valores };
    }
    throw e;
  }
  revalidatePath("/cliente/carrito");
  if (texto(form, "accion") === "comprar") redirect(`/cliente/pago?reservas=${reserva.codigo}`);
  redirect(`/cliente/reservas/${reserva.codigo}?nueva=1`);
}

/** HU-013: paga con el monedero las reservas indicadas. */
export async function pagar(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("CLIENTE");
  const reservas = texto(form, "reservas").split(",").filter(Boolean);
  let pago: Pago;
  try {
    pago = await api<Pago>("/pagos", { metodo: "POST", token: sesion.token, cuerpo: { reservas } });
  } catch (e) {
    return estadoDeError(e);
  }
  revalidatePath("/cliente", "layout");
  redirect(
    pago.reservas.length === 1
      ? `/cliente/reservas/${pago.reservas[0]}?comprada=1`
      : `/cliente/reservas?pagadas=${pago.reservas.join(",")}`,
  );
}

/** HU-015 y HU-016: cancela una compra dentro del plazo o una reserva vigente. */
export async function cancelar(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("CLIENTE");
  const codigo = texto(form, "codigo");
  try {
    await api(`/reservas/${encodeURIComponent(codigo)}/cancelar`, { metodo: "POST", token: sesion.token });
  } catch (e) {
    return estadoDeError(e);
  }
  revalidatePath("/cliente", "layout");
  redirect(`/cliente/reservas/${codigo}?cancelada=1`);
}

/** HU-012: sacar o volver a poner una reserva en el carrito. */
export async function moverEnCarrito(form: FormData) {
  const sesion = await exigirSesion("CLIENTE");
  const codigo = texto(form, "codigo");
  const dentro = texto(form, "dentro") === "1";
  await api(`/carrito/${encodeURIComponent(codigo)}`, { metodo: dentro ? "POST" : "DELETE", token: sesion.token });
  revalidatePath("/cliente/carrito");
  revalidatePath(`/cliente/reservas/${codigo}`);
}

const CAMPOS_TARJETA = ["tipo", "franquicia", "titular", "numero", "vencimiento"] as const;

/** HU-014: registrar una tarjeta (simulada). */
export async function guardarTarjeta(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("CLIENTE");
  const datos: Record<string, string> = {};
  for (const c of CAMPOS_TARJETA) datos[c] = texto(form, c);
  datos.numero = datos.numero.replace(/[\s-]/g, "");
  try {
    await api("/monedero/tarjetas", { metodo: "POST", token: sesion.token, cuerpo: datos });
  } catch (e) {
    return estadoDeError(e, { ...datos, numero: "" });
  }
  revalidatePath("/cliente/monedero");
  return { ok: true, mensaje: "Tarjeta registrada." };
}

export async function quitarTarjeta(form: FormData) {
  const sesion = await exigirSesion("CLIENTE");
  await api(`/monedero/tarjetas/${encodeURIComponent(texto(form, "id"))}`, { metodo: "DELETE", token: sesion.token });
  revalidatePath("/cliente/monedero");
}

/** HU-014: el cliente edita su saldo a mano (RF-70). */
export async function ajustarSaldo(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("CLIENTE");
  const saldo = texto(form, "saldo").replace(/[.\s$]/g, "").replace(",", ".");
  try {
    const m = await api<Monedero>("/monedero/saldo", { metodo: "PUT", token: sesion.token, cuerpo: { saldo } });
    revalidatePath("/cliente", "layout");
    return { ok: true, mensaje: "Saldo actualizado.", valores: { saldo: m.saldo } };
  } catch (e) {
    return estadoDeError(e, { saldo });
  }
}
