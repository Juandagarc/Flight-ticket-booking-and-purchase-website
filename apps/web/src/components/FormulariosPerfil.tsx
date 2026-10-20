"use client";

import { useActionState } from "react";

import { cambiarContrasena, completarPerfil, guardarPerfil } from "@/acciones/perfil";
import type { EstadoFormulario, Perfil } from "@/lib/tipos";

import { BotonEnviar } from "./BotonEnviar";
import { CamposPerfil } from "./CamposPerfil";
import { Aviso, Campo } from "./ui";

function Mensaje({ estado }: { estado: EstadoFormulario }) {
  if (!estado.mensaje) return null;
  return <Aviso tipo={estado.ok ? "exito" : "error"}>{estado.mensaje}</Aviso>;
}

/** HU-003 · Pantalla 36: edición del perfil. El documento se muestra pero no se edita. */
export function FormularioPerfil({ perfil }: { perfil: Perfil }) {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(guardarPerfil, {});
  const valores = estado.ok || !estado.valores ? perfil : { ...perfil, ...estado.valores };
  return (
    <form action={accion} className="flex flex-col gap-4" noValidate>
      <Mensaje estado={estado} />
      <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
        <Campo etiqueta="Tipo de documento" nombre="tipo_documento_ro" value={perfil.tipo_documento === "CEDULA" ? "Cédula" : "Pasaporte"} disabled readOnly />
        <Campo
          etiqueta="Documento"
          nombre="documento_ro"
          value={perfil.documento}
          disabled
          readOnly
          ayuda="El documento identifica tu cuenta y no se puede cambiar."
        />
      </div>
      <CamposPerfil key={JSON.stringify(valores)} valores={valores} campos={estado.campos} conDocumento={false} />
      <BotonEnviar className="self-end">Guardar cambios</BotonEnviar>
    </form>
  );
}

/** HU-003 · El administrador completa su registro con los mismos campos de un cliente. */
export function FormularioCompletarPerfil() {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(completarPerfil, {});
  return (
    <form action={accion} className="flex flex-col gap-4" noValidate>
      <Mensaje estado={estado} />
      <CamposPerfil key={JSON.stringify(estado.valores ?? {})} valores={estado.valores} campos={estado.campos} />
      <BotonEnviar className="self-end">Completar registro</BotonEnviar>
    </form>
  );
}

/** HU-004 · Cambio de contraseña con la actual, la nueva y su confirmación. */
export function FormularioContrasena() {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(cambiarContrasena, {});
  const campos = estado.campos ?? {};
  return (
    <form action={accion} className="flex flex-col gap-4" noValidate key={estado.ok ? "ok" : "editando"}>
      <Mensaje estado={estado} />
      <Campo etiqueta="Contraseña actual" nombre="actual" type="password" autoComplete="current-password" error={campos.actual} required />
      <Campo etiqueta="Nueva contraseña" nombre="nueva" type="password" autoComplete="new-password" error={campos.nueva} required />
      <Campo
        etiqueta="Confirmar nueva contraseña"
        nombre="confirmacion"
        type="password"
        autoComplete="new-password"
        error={campos.confirmacion}
        required
      />
      <BotonEnviar className="self-end">Cambiar contraseña</BotonEnviar>
    </form>
  );
}
