"use client";

import { useActionState } from "react";

import { iniciarSesion } from "@/acciones/auth";
import type { EstadoFormulario } from "@/lib/tipos";

import { BotonEnviar } from "./BotonEnviar";
import { Aviso, Campo } from "./ui";

export function FormularioLogin({ next, usuario }: { next?: string; usuario?: string }) {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(iniciarSesion, {});
  return (
    <form action={accion} className="flex flex-col gap-4" noValidate>
      {estado.mensaje && !estado.ok ? <Aviso tipo="error">{estado.mensaje}</Aviso> : null}
      <input type="hidden" name="next" value={next ?? ""} />
      <Campo
        etiqueta="Usuario"
        nombre="nombre_usuario"
        autoComplete="username"
        required
        defaultValue={estado.valores?.nombre_usuario ?? usuario}
        ayuda="El root ingresa con su Id."
      />
      <Campo etiqueta="Contraseña" nombre="contrasena" type="password" autoComplete="current-password" required />
      <BotonEnviar pendiente="Ingresando…" className="mt-2 w-full">
        Iniciar sesión
      </BotonEnviar>
    </form>
  );
}
