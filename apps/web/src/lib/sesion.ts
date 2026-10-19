import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { leerToken, type DatosSesion } from "./jwt";
import type { Rol } from "./tipos";

export const COOKIE_SESION = "sesion";

export interface Sesion extends DatosSesion {
  token: string;
}

export async function obtenerSesion(): Promise<Sesion | null> {
  const token = (await cookies()).get(COOKIE_SESION)?.value;
  const datos = leerToken(token);
  return datos && token ? { ...datos, token } : null;
}

export async function exigirSesion(...roles: Rol[]): Promise<Sesion> {
  const sesion = await obtenerSesion();
  if (!sesion) redirect("/login");
  if (roles.length && !roles.includes(sesion.rol)) redirect("/");
  return sesion;
}

export async function guardarSesion(token: string) {
  const datos = leerToken(token);
  (await cookies()).set(COOKIE_SESION, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production" && process.env.COOKIE_INSEGURA !== "1",
    path: "/",
    expires: datos ? new Date(datos.exp * 1000) : undefined,
  });
}

export async function borrarSesion() {
  (await cookies()).delete(COOKIE_SESION);
}
