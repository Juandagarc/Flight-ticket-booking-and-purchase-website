import type { Perfil } from "@/lib/tipos";

import { Campo, Seleccion } from "./ui";

type Valores = Partial<Perfil> | Record<string, string | null | undefined>;

/** Campos de datos personales compartidos por el registro y el perfil (RF-28). */
export function CamposPerfil({
  valores = {},
  campos = {},
  conDocumento = true,
}: {
  valores?: Valores;
  campos?: Record<string, string>;
  conDocumento?: boolean;
}) {
  const v = (k: string) => (valores as Record<string, string | null | undefined>)[k] ?? undefined;
  return (
    <>
      {conDocumento ? (
        <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
          <Seleccion etiqueta="Tipo de documento" nombre="tipo_documento" defaultValue={v("tipo_documento") ?? "CEDULA"} error={campos.tipo_documento}>
            <option value="CEDULA">Cédula</option>
            <option value="PASAPORTE">Pasaporte</option>
          </Seleccion>
          <Campo
            etiqueta="Número de documento"
            nombre="documento"
            defaultValue={v("documento")}
            error={campos.documento}
            ayuda="Solo letras y números, sin puntos ni espacios."
            required
          />
        </div>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo etiqueta="Nombres" nombre="nombres" defaultValue={v("nombres")} error={campos.nombres} autoComplete="given-name" required />
        <Campo etiqueta="Apellidos" nombre="apellidos" defaultValue={v("apellidos")} error={campos.apellidos} autoComplete="family-name" required />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Campo
          etiqueta="Fecha de nacimiento"
          nombre="fecha_nacimiento"
          type="date"
          defaultValue={v("fecha_nacimiento")}
          error={campos.fecha_nacimiento}
          required
        />
        <Campo etiqueta="Lugar de nacimiento" nombre="lugar_nacimiento" defaultValue={v("lugar_nacimiento")} error={campos.lugar_nacimiento} required />
        <Seleccion etiqueta="Género" nombre="genero" defaultValue={v("genero") ?? ""} error={campos.genero}>
          <option value="" disabled>
            Selecciona…
          </option>
          <option value="FEMENINO">Femenino</option>
          <option value="MASCULINO">Masculino</option>
          <option value="OTRO">Otro</option>
        </Seleccion>
      </div>
      <Campo
        etiqueta="Dirección de facturación"
        nombre="direccion_facturacion"
        defaultValue={v("direccion_facturacion")}
        error={campos.direccion_facturacion}
        autoComplete="street-address"
        required
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo etiqueta="Correo electrónico" nombre="correo" type="email" defaultValue={v("correo")} error={campos.correo} autoComplete="email" required />
        <Campo
          etiqueta="Imagen de usuario (opcional)"
          nombre="imagen_url"
          type="url"
          placeholder="https://…"
          defaultValue={v("imagen_url")}
          error={campos.imagen_url}
        />
      </div>
    </>
  );
}
