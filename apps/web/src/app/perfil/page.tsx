import type { Metadata } from "next";

import { FormularioCompletarPerfil, FormularioContrasena, FormularioPerfil } from "@/components/FormulariosPerfil";
import { Aviso, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { exigirSesion } from "@/lib/sesion";
import type { UsuarioDetalle } from "@/lib/tipos";

export const metadata: Metadata = { title: "Perfil y contraseña" };

/** HU-003 y HU-004 · Pantalla 36: perfil y contraseña. */
export default async function PaginaPerfil({ searchParams }: { searchParams: Promise<{ completado?: string }> }) {
  const { completado } = await searchParams;
  const sesion = await exigirSesion();
  const yo = await api<UsuarioDetalle>("/auth/me", { token: sesion.token });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <div>
        <Encabezado titulo={yo.rol === "ROOT" ? "Contraseña" : "Perfil"} bajada={`Sesión de ${yo.nombre_usuario}`} />
        {completado && yo.perfil ? (
          <div className="mb-4">
            <Aviso tipo="exito">Tu registro quedó completo.</Aviso>
          </div>
        ) : null}
        {yo.rol === "ROOT" ? (
          <Aviso>El root solo tiene Id y contraseña; no tiene datos personales.</Aviso>
        ) : yo.perfil ? (
          <Tarjeta>
            <h2 className="mb-4 text-lg font-semibold">Datos personales</h2>
            <FormularioPerfil perfil={yo.perfil} />
          </Tarjeta>
        ) : (
          <Tarjeta>
            <h2 className="text-lg font-semibold">Completa tu registro</h2>
            <p className="mb-4 mt-1 text-sm text-tinta-suave">
              Como administrador puedes registrar tus datos personales. Esto no habilita compras ni reservas.
            </p>
            <FormularioCompletarPerfil />
          </Tarjeta>
        )}
      </div>
      <Tarjeta className="h-fit lg:mt-[4.5rem]">
        <h2 className="mb-4 text-lg font-semibold">Cambiar contraseña</h2>
        <FormularioContrasena />
      </Tarjeta>
    </div>
  );
}
