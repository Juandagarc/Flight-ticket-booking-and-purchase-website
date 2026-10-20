"use server";

import { redirect } from "next/navigation";

import { api, estadoDeError } from "@/lib/api";
import { destinoSeguro } from "@/lib/rutas";
import { borrarSesion, guardarSesion } from "@/lib/sesion";
import type { EstadoFormulario, Rol } from "@/lib/tipos";

const CAMPOS_REGISTRO = [
  "documento",
  "tipo_documento",
  "nombres",
  "apellidos",
  "fecha_nacimiento",
  "lugar_nacimiento",
  "direccion_facturacion",
  "genero",
  "correo",
  "imagen_url",
  "nombre_usuario",
] as const;

/** Solo los campos del formulario: el navegador también envía campos internos de Next.js. */
function valoresDe(form: FormData, campos: readonly string[]): Record<string, string> {
  const valores: Record<string, string> = {};
  for (const c of campos) valores[c] = String(form.get(c) ?? "").trim();
  return valores;
}

/** HU-002 · Inicio de sesión: cada rol llega a su propia página. */
export async function iniciarSesion(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const nombre_usuario = String(form.get("nombre_usuario") ?? "").trim();
  const contrasena = String(form.get("contrasena") ?? "");
  let destino: string;
  try {
    const r = await api<{ access_token: string; usuario: { rol: Rol } }>("/auth/login", {
      metodo: "POST",
      cuerpo: { nombre_usuario, contrasena },
    });
    await guardarSesion(r.access_token);
    destino = destinoSeguro(String(form.get("next") ?? ""), r.usuario.rol);
  } catch (e) {
    return estadoDeError(e, { nombre_usuario });
  }
  redirect(destino);
}

/** HU-001 · Registro de cliente. Después del registro el cliente inicia sesión con sus credenciales. */
export async function registrarCliente(_: EstadoFormulario, form: FormData): Promise<EstadoFormulario> {
  const valores = valoresDe(form, CAMPOS_REGISTRO);
  const contrasena = String(form.get("contrasena") ?? "");
  if (contrasena !== String(form.get("confirmacion") ?? "")) {
    return {
      ok: false,
      mensaje: "Revisa los datos marcados.",
      campos: { confirmacion: "Las contraseñas no coinciden." },
      valores,
    };
  }
  const cuerpo: Record<string, string | null> = { ...valores, contrasena, imagen_url: valores.imagen_url || null };
  try {
    await api("/auth/registro", { metodo: "POST", cuerpo });
  } catch (e) {
    return estadoDeError(e, valores);
  }
  redirect(`/login?registrado=1&usuario=${encodeURIComponent(valores.nombre_usuario ?? "")}`);
}

export async function cerrarSesion() {
  await borrarSesion();
  redirect("/");
}
