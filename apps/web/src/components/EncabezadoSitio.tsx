import Link from "next/link";

import { cerrarSesion } from "@/acciones/auth";
import { obtenerSesion } from "@/lib/sesion";
import type { Rol } from "@/lib/tipos";

import { botonClases } from "./ui";

const ENLACES: Record<Rol | "VISITANTE", { href: string; texto: string }[]> = {
  VISITANTE: [
    { href: "/vuelos", texto: "Buscar vuelos" },
    { href: "/noticias", texto: "Noticias" },
  ],
  CLIENTE: [
    { href: "/vuelos", texto: "Buscar vuelos" },
    { href: "/noticias", texto: "Noticias" },
    { href: "/cliente", texto: "Mi cuenta" },
    { href: "/perfil", texto: "Perfil" },
  ],
  ADMINISTRADOR: [
    { href: "/admin/vuelos", texto: "Gestión de vuelos" },
    { href: "/noticias", texto: "Noticias" },
    { href: "/perfil", texto: "Perfil" },
  ],
  ROOT: [
    { href: "/admin/administradores", texto: "Administradores" },
    { href: "/perfil", texto: "Contraseña" },
  ],
};

const NOMBRE_ROL: Record<Rol, string> = { CLIENTE: "Cliente", ADMINISTRADOR: "Administrador", ROOT: "Root" };

export function Marca() {
  return (
    <span className="flex items-center gap-2 text-lg font-bold tracking-tight">
      <svg aria-hidden viewBox="0 0 24 24" className="h-7 w-7 text-cielo" fill="currentColor">
        <path d="M21.5 15.5v-2l-8-5V3a1.5 1.5 0 0 0-3 0v5.5l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5l-2-1.5v-6z" />
      </svg>
      Flight
    </span>
  );
}

export async function EncabezadoSitio() {
  const sesion = await obtenerSesion();
  const enlaces = ENLACES[sesion?.rol ?? "VISITANTE"];
  return (
    <header className="border-b border-linea bg-superficie">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link href="/" aria-label="Flight, inicio">
          <Marca />
        </Link>
        <nav aria-label="Principal" className="order-3 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto">
          {enlaces.map((e) => (
            <Link
              key={e.href}
              href={e.href}
              className="whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium text-tinta-suave hover:bg-fondo hover:text-tinta"
            >
              {e.texto}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {sesion ? (
            <>
              <span className="hidden text-right text-xs leading-tight text-tinta-suave sm:block" data-testid="sesion">
                <span className="block font-semibold text-tinta">{sesion.usuario}</span>
                {NOMBRE_ROL[sesion.rol]}
              </span>
              <form action={cerrarSesion}>
                <button className={botonClases("secundario", "px-3 py-2 text-sm")}>Salir</button>
              </form>
            </>
          ) : (
            <>
              <Link href="/login" className={botonClases("fantasma", "px-3 py-2 text-sm")}>
                Iniciar sesión
              </Link>
              <Link href="/registro" className={botonClases("primario", "px-3 py-2 text-sm")}>
                Registrarse
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
