import Link from "next/link";

import * as f from "@/lib/formato";
import type { Vuelo } from "@/lib/tipos";

import { botonClases } from "./ui";

export function Ruta({ vuelo }: { vuelo: Vuelo }) {
  const dias = f.diasDeDiferencia(vuelo.salida_local, vuelo.llegada_local);
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
      <div>
        <p className="cifra text-2xl font-bold">{f.hora(vuelo.salida_local)}</p>
        <p className="text-sm font-medium">{vuelo.origen.nombre}</p>
        <p className="text-xs text-tinta-suave">{vuelo.origen.codigo}</p>
      </div>
      <div className="flex min-w-24 flex-col items-center text-xs text-tinta-suave">
        <span>{f.duracion(vuelo.duracion_min)}</span>
        <span aria-hidden className="relative my-1 block h-px w-full bg-linea">
          <span className="absolute -top-1 right-0 h-2 w-2 rounded-full bg-cielo" />
        </span>
        <span>Directo</span>
      </div>
      <div className="text-right">
        <p className="cifra text-2xl font-bold">
          {f.hora(vuelo.llegada_local)}
          {dias > 0 ? <sup className="ml-0.5 text-xs font-semibold text-atardecer">+{dias}</sup> : null}
        </p>
        <p className="text-sm font-medium">{vuelo.destino.nombre}</p>
        <p className="text-xs text-tinta-suave">{vuelo.destino.codigo} · hora local</p>
      </div>
    </div>
  );
}

export function TarjetaVuelo({ vuelo, pasajeros }: { vuelo: Vuelo; pasajeros?: number }) {
  const reservar = `/reservar/${vuelo.codigo}${pasajeros ? `?pasajeros=${pasajeros}` : ""}`;
  return (
    <article
      data-testid="resultado-vuelo"
      className="grid gap-5 rounded-2xl border border-linea bg-superficie p-5 md:grid-cols-[1fr_auto] md:items-center"
    >
      <div>
        <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-tinta-suave">
          <span className="rounded-md bg-fondo px-2 py-1 font-semibold text-tinta">{vuelo.codigo}</span>
          <span>{f.fechaCorta(vuelo.salida_local)}</span>
          <span>·</span>
          <span>{vuelo.tipo === "NACIONAL" ? "Nacional" : "Internacional"}</span>
        </div>
        <Ruta vuelo={vuelo} />
      </div>
      <div className="flex flex-col gap-3 border-t border-linea pt-4 md:min-w-56 md:border-l md:border-t-0 md:pl-5 md:pt-0">
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-xs text-tinta-suave">Económica</dt>
            <dd className="cifra font-bold text-tinta">{f.precio(vuelo.tarifas.economica)}</dd>
          </div>
          <div>
            <dt className="text-xs text-tinta-suave">Primera</dt>
            <dd className="cifra font-bold text-tinta">{f.precio(vuelo.tarifas.primera)}</dd>
          </div>
        </dl>
        <Link href={reservar} className={botonClases("primario", "w-full")}>
          Reservar
        </Link>
      </div>
    </article>
  );
}
