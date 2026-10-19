"use client";

import { useActionState, useMemo, useState } from "react";

import type { Ciudad, EstadoFormulario } from "@/lib/tipos";

import { BotonEnviar } from "./BotonEnviar";
import { Aviso, Campo, Seleccion } from "./ui";

export interface ValoresVuelo {
  origen: string;
  destino: string;
  fecha_salida: string;
  hora_salida: string;
  tarifa_primera: string;
  tarifa_economica: string;
  imagen_url: string;
}

type Accion = (estado: EstadoFormulario, form: FormData) => Promise<EstadoFormulario>;

/** Destinos válidos para un origen (RF-03 a RF-05, RF-49). */
export function destinosPermitidos(ciudades: Ciudad[], origen: string): Ciudad[] {
  const o = ciudades.find((c) => c.codigo === origen);
  if (!o) return [];
  return ciudades.filter(
    (c) =>
      c.codigo !== o.codigo &&
      ((o.es_capital_nacional && c.es_capital_nacional) || (o.origen_internacional && c.destino_internacional)),
  );
}

/** HU-006 y HU-007 · Pantallas 27 y 28. El código, el tiempo de vuelo y la llegada los calcula el sistema. */
export function FormularioVuelo({
  accion,
  ciudades,
  inicial,
  textoBoton,
}: {
  accion: Accion;
  ciudades: Ciudad[];
  inicial?: Partial<ValoresVuelo>;
  textoBoton: string;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(accion, {});
  const valores = { ...inicial, ...estado.valores } as Partial<ValoresVuelo>;
  const campos = estado.campos ?? {};
  const [origen, setOrigen] = useState(valores.origen ?? "");
  const [destino, setDestino] = useState(valores.destino ?? "");
  const destinos = useMemo(() => destinosPermitidos(ciudades, origen), [ciudades, origen]);
  const origenes = ciudades.filter((c) => c.es_capital_nacional);
  const nacionales = destinos.filter((c) => c.es_capital_nacional);
  const internacionales = destinos.filter((c) => !c.es_capital_nacional);

  return (
    <form action={enviar} className="flex flex-col gap-5" noValidate>
      {estado.mensaje && !estado.ok ? <Aviso tipo="error">{estado.mensaje}</Aviso> : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <Seleccion
          etiqueta="Origen"
          nombre="origen"
          value={origen}
          onChange={(e) => {
            setOrigen(e.target.value);
            setDestino("");
          }}
          error={campos.origen}
        >
          <option value="" disabled>
            Selecciona la ciudad de origen
          </option>
          {origenes.map((c) => (
            <option key={c.codigo} value={c.codigo}>
              {c.nombre} ({c.codigo}){c.origen_internacional ? " · nacional e internacional" : ""}
            </option>
          ))}
        </Seleccion>
        <Seleccion
          etiqueta="Destino"
          nombre="destino"
          value={destino}
          onChange={(e) => setDestino(e.target.value)}
          disabled={!origen}
          error={campos.destino}
          ayuda={origen && internacionales.length === 0 ? "Desde esta ciudad solo hay vuelos nacionales." : undefined}
        >
          <option value="" disabled>
            {origen ? "Selecciona el destino" : "Primero escoge el origen"}
          </option>
          <optgroup label="Nacional">
            {nacionales.map((c) => (
              <option key={c.codigo} value={c.codigo}>
                {c.nombre} ({c.codigo})
              </option>
            ))}
          </optgroup>
          {internacionales.length > 0 ? (
            <optgroup label="Internacional">
              {internacionales.map((c) => (
                <option key={c.codigo} value={c.codigo}>
                  {c.nombre}, {c.pais} ({c.codigo})
                </option>
              ))}
            </optgroup>
          ) : null}
        </Seleccion>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo
          etiqueta="Fecha de salida"
          nombre="fecha_salida"
          type="date"
          defaultValue={valores.fecha_salida}
          error={campos.fecha_salida}
          required
        />
        <Campo
          etiqueta="Hora de salida"
          nombre="hora_salida"
          type="time"
          defaultValue={valores.hora_salida}
          error={campos.hora_salida}
          ayuda="Hora local de la ciudad de origen."
          required
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo
          etiqueta="Tarifa primera clase (COP por persona)"
          nombre="tarifa_primera"
          type="number"
          min={1}
          step={1}
          inputMode="numeric"
          defaultValue={valores.tarifa_primera}
          error={campos.tarifa_primera}
          required
        />
        <Campo
          etiqueta="Tarifa económica (COP por persona)"
          nombre="tarifa_economica"
          type="number"
          min={1}
          step={1}
          inputMode="numeric"
          defaultValue={valores.tarifa_economica}
          error={campos.tarifa_economica}
          required
        />
      </div>
      <Campo
        etiqueta="Imagen alusiva (opcional)"
        nombre="imagen_url"
        type="url"
        placeholder="https://… — si la dejas vacía se usa la imagen del destino"
        defaultValue={valores.imagen_url}
        error={campos.imagen_url}
      />
      <p className="rounded-lg bg-fondo px-4 py-3 text-sm text-tinta-suave">
        El código del vuelo, el tiempo de vuelo y la hora local de llegada los calcula el sistema al guardar.
      </p>
      <BotonEnviar className="self-end">{textoBoton}</BotonEnviar>
    </form>
  );
}
