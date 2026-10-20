"use client";

import { useActionState } from "react";

import { crearAdministrador } from "@/acciones/admin";
import type { EstadoFormulario } from "@/lib/tipos";

import { BotonEnviar } from "./BotonEnviar";
import { Aviso, Campo } from "./ui";

/** HU-005 · Pantalla 38: crear administrador. */
export function FormularioAdministrador() {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(crearAdministrador, {});
  const campos = estado.campos ?? {};
  return (
    <form action={accion} className="flex flex-col gap-4" noValidate key={estado.ok ? estado.mensaje : "form"}>
      {estado.mensaje ? <Aviso tipo={estado.ok ? "exito" : "error"}>{estado.mensaje}</Aviso> : null}
      <Campo
        etiqueta="Usuario"
        nombre="nombre_usuario"
        defaultValue={estado.ok ? "" : estado.valores?.nombre_usuario}
        error={campos.nombre_usuario}
        autoComplete="off"
        required
      />
      <Campo
        etiqueta="Contraseña inicial"
        nombre="contrasena"
        type="password"
        error={campos.contrasena}
        autoComplete="new-password"
        ayuda="El administrador puede cambiarla después desde su perfil."
        required
      />
      <BotonEnviar className="self-end">Crear administrador</BotonEnviar>
    </form>
  );
}
