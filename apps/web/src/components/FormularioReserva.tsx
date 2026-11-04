"use client";

import { useActionState, useState } from "react";
import { useFormStatus } from "react-dom";

import { reservar } from "@/acciones/compras";
import * as f from "@/lib/formato";
import type { Clase, EstadoFormulario, Perfil, Vuelo } from "@/lib/tipos";

import { Aviso, Boton, Campo, cx, Seleccion } from "./ui";

function Botones() {
  const { pending } = useFormStatus();
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
      <Boton type="submit" name="accion" value="reservar" variante="secundario" disabled={pending}>
        {pending ? "Procesando…" : "Agregar al carrito (reservar)"}
      </Boton>
      <Boton type="submit" name="accion" value="comprar" disabled={pending}>
        {pending ? "Procesando…" : "Comprar ahora"}
      </Boton>
    </div>
  );
}

function Viajero({
  i,
  valores,
  campos,
}: {
  i: number;
  valores: Record<string, string | undefined>;
  campos: Record<string, string>;
}) {
  const n = (c: string) => `p${i}_${c}`;
  const v = (c: string) => valores[n(c)];
  return (
    <fieldset className="flex flex-col gap-4 rounded-xl border border-linea p-4" data-testid="viajero">
      <legend className="px-1 text-sm font-semibold">Viajero {i + 1}</legend>
      <div className="grid gap-4 sm:grid-cols-3">
        <Campo etiqueta="Documento" nombre={n("documento")} defaultValue={v("documento")} error={campos[n("documento")]} required />
        <Campo etiqueta="Nombres" nombre={n("nombres")} defaultValue={v("nombres")} error={campos[n("nombres")]} required />
        <Campo etiqueta="Apellidos" nombre={n("apellidos")} defaultValue={v("apellidos")} error={campos[n("apellidos")]} required />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Campo
          etiqueta="Fecha de nacimiento"
          nombre={n("fecha_nacimiento")}
          type="date"
          defaultValue={v("fecha_nacimiento")}
          error={campos[n("fecha_nacimiento")]}
          required
        />
        <Seleccion etiqueta="Género" nombre={n("genero")} defaultValue={v("genero") ?? ""} error={campos[n("genero")]}>
          <option value="" disabled>
            Selecciona
          </option>
          <option value="FEMENINO">Femenino</option>
          <option value="MASCULINO">Masculino</option>
          <option value="OTRO">Otro</option>
        </Seleccion>
        <Campo etiqueta="Teléfono" nombre={n("telefono")} type="tel" defaultValue={v("telefono")} error={campos[n("telefono")]} required />
      </div>
      <Campo etiqueta="Correo" nombre={n("correo")} type="email" defaultValue={v("correo")} error={campos[n("correo")]} required />
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo
          etiqueta="Contacto de emergencia"
          nombre={n("nombre_contacto")}
          defaultValue={v("nombre_contacto")}
          error={campos[n("nombre_contacto")]}
          required
        />
        <Campo
          etiqueta="Teléfono del contacto"
          nombre={n("telefono_contacto")}
          type="tel"
          defaultValue={v("telefono_contacto")}
          error={campos[n("telefono_contacto")]}
          required
        />
      </div>
    </fieldset>
  );
}

/** HU-010 · Pantallas 12 y 13: clase, trayecto y datos de cada viajero. */
export function FormularioReserva({
  vuelo,
  regresos,
  perfil,
  pasajerosIniciales,
}: {
  vuelo: Vuelo;
  regresos: Vuelo[];
  perfil: Perfil | null;
  pasajerosIniciales: number;
}) {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(reservar, {});
  const previos = estado.valores ?? {};
  const [cantidad, setCantidad] = useState(Number(previos.cantidad) || pasajerosIniciales);
  const [clase, setClase] = useState<Clase>((previos.clase as Clase) || "ECONOMICA");
  const [trayecto, setTrayecto] = useState(previos.trayecto || "SENCILLO");
  const [regreso, setRegreso] = useState(previos.regreso || "");
  const campos = estado.campos ?? {};

  const valores: Record<string, string | undefined> = estado.valores
    ? estado.valores
    : perfil
      ? {
          p0_documento: perfil.documento,
          p0_nombres: perfil.nombres,
          p0_apellidos: perfil.apellidos,
          p0_fecha_nacimiento: perfil.fecha_nacimiento,
          p0_genero: perfil.genero,
          p0_correo: perfil.correo,
        }
      : {};

  const vueloRegreso = regresos.find((r) => r.codigo === regreso);
  const tarifa = (v: Vuelo) => Number(clase === "PRIMERA" ? v.tarifas.primera : v.tarifas.economica);
  const total = cantidad * (tarifa(vuelo) + (trayecto === "IDA_Y_VUELTA" && vueloRegreso ? tarifa(vueloRegreso) : 0));
  const sinCupo = (v: Vuelo) => (clase === "PRIMERA" ? v.disponibles.primera : v.disponibles.economica) < cantidad;

  return (
    <form action={accion} className="flex flex-col gap-6" noValidate key={JSON.stringify(estado)}>
      <input type="hidden" name="vuelo" value={vuelo.codigo} />
      <input type="hidden" name="clase" value={clase} />
      <input type="hidden" name="cantidad" value={cantidad} />
      <input type="hidden" name="trayecto" value={trayecto} />
      <input type="hidden" name="regreso" value={trayecto === "IDA_Y_VUELTA" ? regreso : ""} />
      {estado.mensaje ? <Aviso tipo="error">{estado.mensaje}</Aviso> : null}

      <section className="flex flex-col gap-3">
        <h2 className="font-semibold">Clase</h2>
        <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Clase">
          {(["ECONOMICA", "PRIMERA"] as const).map((c) => {
            const libres = c === "PRIMERA" ? vuelo.disponibles.primera : vuelo.disponibles.economica;
            return (
              <button
                key={c}
                type="button"
                role="radio"
                aria-checked={clase === c}
                onClick={() => setClase(c)}
                className={cx(
                  "rounded-xl border p-4 text-left transition",
                  clase === c ? "border-cielo bg-cielo-claro ring-2 ring-cielo/20" : "border-linea hover:border-tinta-suave",
                )}
              >
                <span className="block text-sm font-semibold">{f.CLASE[c]}</span>
                <span className="cifra block text-xl font-bold">
                  {f.precio(c === "PRIMERA" ? vuelo.tarifas.primera : vuelo.tarifas.economica)}
                </span>
                <span className="block text-xs text-tinta-suave">
                  {libres} {libres === 1 ? "silla disponible" : "sillas disponibles"}
                </span>
              </button>
            );
          })}
        </div>
        <p className="text-xs text-tinta-suave">La silla se asigna al azar dentro de la clase elegida.</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <Seleccion
          etiqueta="Trayecto"
          nombre="trayecto_visible"
          value={trayecto}
          onChange={(e) => setTrayecto(e.target.value)}
          ayuda={regresos.length === 0 ? "No hay vuelos de regreso programados para esta ruta." : undefined}
        >
          <option value="SENCILLO">Solo ida</option>
          <option value="IDA_Y_VUELTA" disabled={regresos.length === 0}>
            Ida y vuelta
          </option>
        </Seleccion>
        <Seleccion
          etiqueta="Viajeros"
          nombre="cantidad_visible"
          value={cantidad}
          onChange={(e) => setCantidad(Number(e.target.value))}
          ayuda="Máximo 5 tiquetes por vuelo."
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </Seleccion>
      </section>

      {trayecto === "IDA_Y_VUELTA" ? (
        <Seleccion
          etiqueta="Vuelo de regreso"
          nombre="regreso_visible"
          value={regreso}
          onChange={(e) => setRegreso(e.target.value)}
          error={campos.regreso ?? campos.vuelo_regreso_codigo}
        >
          <option value="">Selecciona el regreso</option>
          {regresos.map((r) => (
            <option key={r.codigo} value={r.codigo}>
              {r.codigo} · {f.fechaHora(r.salida_local)} · {f.precio(clase === "PRIMERA" ? r.tarifas.primera : r.tarifas.economica)}
            </option>
          ))}
        </Seleccion>
      ) : null}

      {sinCupo(vuelo) || (vueloRegreso && trayecto === "IDA_Y_VUELTA" && sinCupo(vueloRegreso)) ? (
        <Aviso tipo="error">No hay sillas suficientes en {f.CLASE[clase].toLowerCase()} para {cantidad} viajeros.</Aviso>
      ) : null}

      <section className="flex flex-col gap-4">
        <div>
          <h2 className="font-semibold">Datos de los viajeros</h2>
          <p className="text-sm text-tinta-suave">
            Puedes reservar para otras personas. Un menor de edad debe viajar con al menos un adulto.
          </p>
        </div>
        {Array.from({ length: cantidad }, (_, i) => (
          <Viajero key={i} i={i} valores={valores} campos={campos} />
        ))}
      </section>

      <div className="flex flex-col gap-4 border-t border-linea pt-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-tinta-suave">Total</p>
          <p className="cifra text-2xl font-bold" data-testid="total-reserva">
            {f.precio(total)}
          </p>
          <p className="text-xs text-tinta-suave">Una reserva sin pagar se libera a las 24 horas.</p>
        </div>
        <Botones />
      </div>
    </form>
  );
}
