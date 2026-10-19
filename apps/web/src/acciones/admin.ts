"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { api, estadoDeError } from "@/lib/api";
import { exigirSesion } from "@/lib/sesion";
import type { EstadoFormulario, Vuelo } from "@/lib/tipos";

/** HU-005 · El root crea administradores con usuario y contraseña inicial. */
export async function crearAdministrador(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("ROOT");
  const nombre_usuario = String(form.get("nombre_usuario") ?? "").trim();
  const contrasena = String(form.get("contrasena") ?? "");
  try {
    await api("/administradores", { metodo: "POST", cuerpo: { nombre_usuario, contrasena }, token: sesion.token });
  } catch (e) {
    return estadoDeError(e, { nombre_usuario });
  }
  revalidatePath("/admin/administradores");
  return { ok: true, mensaje: `Administrador «${nombre_usuario}» creado.` };
}

const CAMPOS_VUELO = ["origen", "destino", "fecha_salida", "hora_salida", "tarifa_primera", "tarifa_economica", "imagen_url"];

function leerVuelo(form: FormData) {
  const valores: Record<string, string> = {};
  for (const c of CAMPOS_VUELO) valores[c] = String(form.get(c) ?? "").trim();
  return valores;
}

function cuerpoVuelo(valores: Record<string, string>) {
  const cuerpo: Record<string, string | null> = { ...valores };
  cuerpo.imagen_url = valores.imagen_url || null;
  for (const k of ["tarifa_primera", "tarifa_economica"]) cuerpo[k] = valores[k].replace(/[\s$]/g, "");
  return cuerpo;
}

/** HU-006 · Programar vuelo. El código, el tiempo y la llegada los calcula la API. */
export async function programarVuelo(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("ADMINISTRADOR");
  const valores = leerVuelo(form);
  let vuelo: Vuelo;
  try {
    vuelo = await api<Vuelo>("/vuelos", { metodo: "POST", cuerpo: cuerpoVuelo(valores), token: sesion.token });
  } catch (e) {
    return estadoDeError(e, valores);
  }
  revalidatePath("/admin/vuelos");
  redirect(`/admin/vuelos?programado=${vuelo.codigo}`);
}

/** HU-007 · Editar vuelo. Se envían solo los datos editables. */
export async function editarVuelo(codigo: string, _: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("ADMINISTRADOR");
  const valores = leerVuelo(form);
  const cuerpo = cuerpoVuelo(valores);
  if (!cuerpo.imagen_url) delete cuerpo.imagen_url;
  try {
    await api<Vuelo>(`/vuelos/${encodeURIComponent(codigo)}`, { metodo: "PUT", cuerpo, token: sesion.token });
  } catch (e) {
    return estadoDeError(e, valores);
  }
  revalidatePath("/admin/vuelos");
  redirect(`/admin/vuelos?editado=${codigo}`);
}
