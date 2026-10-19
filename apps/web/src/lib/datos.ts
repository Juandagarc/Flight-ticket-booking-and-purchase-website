import "server-only";

import { api, ApiError } from "./api";
import type { Ciudad, Noticia } from "./tipos";

export async function obtenerCiudades(): Promise<Ciudad[]> {
  try {
    return await api<Ciudad[]>("/ciudades");
  } catch (e) {
    if (e instanceof ApiError) return [];
    throw e;
  }
}

export async function obtenerNoticias(limite = 50, tipo?: string): Promise<{ noticias: Noticia[]; error?: string }> {
  try {
    return { noticias: await api<Noticia[]>("/noticias", { consulta: { limite, tipo } }) };
  } catch (e) {
    if (e instanceof ApiError) return { noticias: [], error: e.message };
    throw e;
  }
}
