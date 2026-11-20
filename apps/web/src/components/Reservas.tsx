import Link from "next/link";
import type { ReactNode } from "react";

import * as f from "@/lib/formato";
import type { ReservaResumen, Tramo } from "@/lib/tipos";

import { cx } from "./ui";

const COLOR_ESTADO: Record<string, string> = {
  RESERVADA: "bg-cielo-claro text-cielo-oscuro",
  PAGADA: "bg-exito-claro text-exito",
  CANCELADA: "bg-error-claro text-error",
  VENCIDA: "bg-fondo text-tinta-suave",
};

export function EstadoReserva({ estado }: { estado: string }) {
  return (
    <span className={cx("rounded-md px-2 py-1 text-xs font-semibold", COLOR_ESTADO[estado])} data-testid="estado-reserva">
      {f.ESTADO_RESERVA[estado] ?? estado}
    </span>
  );
}

export function LineaTramo({ tramo, conPrecio = true }: { tramo: Tramo; conPrecio?: boolean }) {
  return (
    <div className="grid gap-1 text-sm sm:grid-cols-[1fr_auto] sm:items-center">
      <div>
        <p className="font-medium">
          {tramo.origen.nombre} → {tramo.destino.nombre}
        </p>
        <p className="text-xs text-tinta-suave">
          {tramo.vuelo_codigo} · {f.fechaHora(tramo.salida_local)} · {f.CLASE[tramo.clase]}
        </p>
      </div>
      {conPrecio ? (
        <p className="cifra text-right text-sm">
          {tramo.viajeros} × {f.precio(tramo.precio_unitario)} = <strong>{f.precio(tramo.subtotal)}</strong>
        </p>
      ) : null}
    </div>
  );
}

/** Tarjeta de una reserva en el carrito o en el histórico. */
export function TarjetaReserva({ reserva, acciones }: { reserva: ReservaResumen; acciones?: ReactNode }) {
  return (
    <article className="flex flex-col gap-4 rounded-2xl border border-linea bg-superficie p-5" data-testid="reserva">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Link href={`/cliente/reservas/${reserva.codigo}`} className="cifra text-lg font-bold hover:text-cielo">
            {reserva.codigo}
          </Link>
          <EstadoReserva estado={reserva.estado} />
          <span className="text-xs text-tinta-suave">
            {reserva.tipo_trayecto === "IDA_Y_VUELTA" ? "Ida y vuelta" : "Solo ida"} · {reserva.viajeros}{" "}
            {reserva.viajeros === 1 ? "viajero" : "viajeros"}
          </span>
        </div>
        <p className="cifra text-lg font-bold">{f.precio(reserva.total)}</p>
      </div>
      <div className="flex flex-col gap-3">
        {reserva.tramos.map((t) => (
          <LineaTramo key={t.vuelo_codigo} tramo={t} />
        ))}
      </div>
      {reserva.estado === "RESERVADA" && reserva.fecha_expiracion ? (
        <p className="text-xs text-atardecer">Vence el {f.momento(reserva.fecha_expiracion)} si no se paga.</p>
      ) : null}
      {acciones ? <div className="flex flex-wrap justify-end gap-2 border-t border-linea pt-4">{acciones}</div> : null}
    </article>
  );
}
