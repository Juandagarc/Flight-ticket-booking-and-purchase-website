"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { api, estadoDeError } from "@/lib/api";
import { exigirSesion } from "@/lib/sesion";
import type { EstadoFormulario } from "@/lib/tipos";

const EDITABLES = [
  "nombres",
  "apellidos",
  "fecha_nacimiento",
  "lugar_nacimiento",
  "direccion_facturacion",
  "genero",
  "correo",
  "imagen_url",
] as const;

function leer(form: FormData, campos: readonly string[]) {
  const datos: Record<string, string | null> = {};
  for (const c of campos) datos[c] = String(form.get(c) ?? "").trim();
  datos.imagen_url = datos.imagen_url || null;
  return datos;
}

/** HU-003 · Edición del perfil (el documento no se envía: no se edita). */
export async function guardarPerfil(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("CLIENTE", "ADMINISTRADOR");
  const datos = leer(form, EDITABLES);
  try {
    await api("/usuarios/me/perfil", { metodo: "PUT", cuerpo: datos, token: sesion.token });
  } catch (e) {
    return estadoDeError(e, datos as Record<string, string>);
  }
  revalidatePath("/perfil");
  return { ok: true, mensaje: "Tus datos quedaron guardados." };
}

/** HU-003 · El administrador completa su registro con los campos de un cliente (RF-32). */
export async function completarPerfil(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion("ADMINISTRADOR");
  const datos = leer(form, [...EDITABLES, "documento", "tipo_documento"]);
  try {
    await api("/usuarios/me/perfil", { metodo: "POST", cuerpo: datos, token: sesion.token });
  } catch (e) {
    return estadoDeError(e, datos as Record<string, string>);
  }
  redirect("/perfil?completado=1");
}

/** HU-004 · Cambio de contraseña. */
export async function cambiarContrasena(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const sesion = await exigirSesion();
  const cuerpo = {
    actual: String(form.get("actual") ?? ""),
    nueva: String(form.get("nueva") ?? ""),
    confirmacion: String(form.get("confirmacion") ?? ""),
  };
  try {
    await api("/usuarios/me/contrasena", { metodo: "PUT", cuerpo, token: sesion.token });
  } catch (e) {
    return estadoDeError(e);
  }
  return { ok: true, mensaje: "Contraseña actualizada. Desde ahora ingresa con la nueva." };
}
