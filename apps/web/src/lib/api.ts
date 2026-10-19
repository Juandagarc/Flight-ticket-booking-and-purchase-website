import "server-only";

import type { EstadoFormulario } from "./tipos";

export const API_URL = process.env.API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public estado: number,
    public codigo: string,
    mensaje: string,
    public campos: Record<string, string> = {},
  ) {
    super(mensaje);
  }
}

interface Opciones {
  metodo?: "GET" | "POST" | "PUT" | "DELETE";
  cuerpo?: unknown;
  token?: string | null;
  consulta?: Record<string, string | number | undefined | null>;
}

export async function api<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const url = new URL(ruta, API_URL);
  for (const [k, v] of Object.entries(opciones.consulta ?? {})) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  }
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opciones.cuerpo !== undefined) headers["Content-Type"] = "application/json";
  if (opciones.token) headers.Authorization = `Bearer ${opciones.token}`;

  let respuesta: Response;
  try {
    respuesta = await fetch(url, {
      method: opciones.metodo ?? "GET",
      headers,
      body: opciones.cuerpo === undefined ? undefined : JSON.stringify(opciones.cuerpo),
      cache: "no-store",
    });
  } catch {
    throw new ApiError(503, "API_NO_DISPONIBLE", "No pudimos conectar con el servidor. Intenta de nuevo.");
  }

  if (respuesta.status === 204) return undefined as T;
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const detalle = datos?.detail ?? {};
    const campos: Record<string, string> = {};
    for (const c of detalle.campos ?? []) {
      if (c?.campo && !campos[c.campo]) campos[c.campo] = c.mensaje;
    }
    throw new ApiError(
      respuesta.status,
      detalle.codigo ?? "ERROR",
      detalle.mensaje ?? "Ocurrió un error inesperado.",
      campos,
    );
  }
  return datos as T;
}

/** Convierte un error de la API en el estado que muestran los formularios. */
export function estadoDeError(error: unknown, valores?: Record<string, string>): EstadoFormulario {
  if (error instanceof ApiError) {
    return { ok: false, mensaje: error.message, campos: error.campos, valores };
  }
  throw error;
}
