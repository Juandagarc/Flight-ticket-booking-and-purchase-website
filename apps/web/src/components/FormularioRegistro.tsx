"use client";

import { useActionState } from "react";

import { registrarCliente } from "@/acciones/auth";
import type { EstadoFormulario } from "@/lib/tipos";

import { BotonEnviar } from "./BotonEnviar";
import { CamposPerfil } from "./CamposPerfil";
import { Aviso, Campo } from "./ui";

/** HU-001 · Pantalla 05: registro de cliente. */
export function FormularioRegistro() {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(registrarCliente, {});
  const campos = estado.campos ?? {};
  const yaRegistrado = campos.documento && estado.mensaje?.includes("Inicia sesión");
  return (
    <form action={accion} className="flex flex-col gap-5" noValidate>
      {estado.mensaje && !estado.ok ? (
        <Aviso tipo="error">
          {estado.mensaje}{" "}
          {yaRegistrado ? (
            <a href="/login" className="font-semibold underline">
              Ir a iniciar sesión
            </a>
          ) : null}
        </Aviso>
      ) : null}
      <fieldset className="flex flex-col gap-4">
        <legend className="mb-2 text-sm font-semibold uppercase tracking-wide text-tinta-suave">Datos personales</legend>
        <CamposPerfil key={JSON.stringify(estado.valores ?? {})} valores={estado.valores} campos={campos} />
      </fieldset>
      <fieldset className="flex flex-col gap-4">
        <legend className="mb-2 text-sm font-semibold uppercase tracking-wide text-tinta-suave">Cuenta</legend>
        <Campo
          etiqueta="Usuario"
          nombre="nombre_usuario"
          defaultValue={estado.valores?.nombre_usuario}
          error={campos.nombre_usuario}
          autoComplete="username"
          required
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo etiqueta="Contraseña" nombre="contrasena" type="password" error={campos.contrasena} autoComplete="new-password" required />
          <Campo
            etiqueta="Confirmar contraseña"
            nombre="confirmacion"
            type="password"
            error={campos.confirmacion}
            autoComplete="new-password"
            required
          />
        </div>
      </fieldset>
      <BotonEnviar pendiente="Creando cuenta…" className="w-full sm:w-auto sm:self-end">
        Crear cuenta
      </BotonEnviar>
    </form>
  );
}
