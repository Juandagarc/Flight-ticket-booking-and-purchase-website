import type { Metadata } from "next";
import Link from "next/link";

import { Aviso, Encabezado, Tarjeta } from "@/components/ui";
import { exigirSesion } from "@/lib/sesion";

export const metadata: Metadata = { title: "Administración" };

function Acceso({ href, titulo, texto }: { href: string; titulo: string; texto: string }) {
  return (
    <Link href={href} className="block">
      <Tarjeta className="h-full transition hover:border-cielo">
        <h2 className="font-semibold">{titulo}</h2>
        <p className="mt-1 text-sm text-tinta-suave">{texto}</p>
      </Tarjeta>
    </Link>
  );
}

/** Panel de administración: destino del administrador y del root tras iniciar sesión (HU-002). */
export default async function PanelAdmin({ searchParams }: { searchParams: Promise<{ aviso?: string }> }) {
  const sesion = await exigirSesion("ADMINISTRADOR", "ROOT");
  const { aviso } = await searchParams;
  return (
    <div className="flex flex-col gap-6">
      <Encabezado
        titulo="Panel de administración"
        bajada={sesion.rol === "ROOT" ? "Sesión de root" : `Administrador ${sesion.usuario}`}
      />
      {aviso === "sin-compras" ? (
        <Aviso tipo="error">Con el rol de {sesion.rol === "ROOT" ? "root" : "administrador"} no se puede reservar ni comprar tiquetes.</Aviso>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sesion.rol === "ROOT" ? (
          <Acceso href="/admin/administradores" titulo="Administradores" texto="Crear cuentas de administrador." />
        ) : (
          <>
            <Acceso href="/admin/vuelos" titulo="Gestión de vuelos" texto="Consultar, programar y editar vuelos." />
            <Acceso href="/admin/vuelos/nuevo" titulo="Programar vuelo" texto="Nuevo vuelo nacional o internacional." />
          </>
        )}
        <Acceso href="/perfil" titulo={sesion.rol === "ROOT" ? "Contraseña" : "Perfil y contraseña"} texto="Tus datos de acceso." />
      </div>
    </div>
  );
}
