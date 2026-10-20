import type { Rol } from "./tipos";

export interface DatosSesion {
  sub: string;
  rol: Rol;
  usuario: string;
  exp: number;
}

function base64UrlADecodificado(parte: string): string {
  const base64 = parte.replace(/-/g, "+").replace(/_/g, "/");
  const relleno = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  const binario = atob(relleno);
  const bytes = Uint8Array.from(binario, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

/**
 * Lee el contenido del token sin verificar la firma: solo sirve para decidir qué mostrar.
 * La API verifica la firma y el rol en cada solicitud.
 */
export function leerToken(token: string | undefined | null, ahora = Date.now()): DatosSesion | null {
  if (!token) return null;
  const partes = token.split(".");
  if (partes.length !== 3) return null;
  try {
    const datos = JSON.parse(base64UrlADecodificado(partes[1])) as Partial<DatosSesion>;
    if (!datos.sub || !datos.rol || !datos.exp) return null;
    if (datos.exp * 1000 <= ahora) return null;
    return datos as DatosSesion;
  } catch {
    return null;
  }
}
