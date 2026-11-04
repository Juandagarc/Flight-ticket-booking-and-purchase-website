import type { Metadata } from "next";
import Link from "next/link";

import { FormularioPago } from "@/components/FormulariosCompra";
import { LineaTramo } from "@/components/Reservas";
import { Aviso, botonClases, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Carrito, ReservaResumen } from "@/lib/tipos";

export const metadata: Metadata = { title: "Pago" };

/** HU-011 y HU-013 · Pantalla 15: resumen de la compra y pago con el monedero. */
export default async function PaginaPago({ searchParams }: { searchParams: Promise<{ reservas?: string }> }) {
  const { reservas: elegidas } = await searchParams;
  const sesion = await exigirSesion("CLIENTE");
  const carrito = await api<Carrito>("/carrito", { token: sesion.token });
  const codigos = elegidas?.split(",").map((c) => c.trim().toUpperCase()).filter(Boolean);

  let reservas: ReservaResumen[] = carrito.reservas;
  if (codigos?.length) {
    reservas = await Promise.all(
      codigos.map((c) => api<ReservaResumen>(`/reservas/${encodeURIComponent(c)}`, { token: sesion.token })),
    );
  }
  const pagables = reservas.filter((r) => r.puede_pagar);
  const total = pagables.reduce((s, r) => s + Number(r.total), 0);
  const saldo = Number(carrito.saldo);
  const alcanza = saldo >= total;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Encabezado titulo="Confirmar compra" bajada="El pago se hace con el saldo de tu monedero." />
      {pagables.length === 0 ? (
        <Tarjeta className="flex flex-col items-start gap-4">
          <p className="text-tinta-suave">No hay reservas pendientes de pago.</p>
          <Link href="/cliente/reservas" className={botonClases("secundario")}>
            Ver mis reservas
          </Link>
        </Tarjeta>
      ) : (
        <Tarjeta className="flex flex-col gap-5">
          {pagables.map((r) => (
            <div key={r.codigo} className="flex flex-col gap-2 border-b border-linea pb-4">
              <p className="cifra text-sm font-semibold">Reserva {r.codigo}</p>
              {r.tramos.map((t) => (
                <LineaTramo key={t.vuelo_codigo} tramo={t} />
              ))}
            </div>
          ))}
          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between text-base font-bold">
              <dt>Total a pagar</dt>
              <dd className="cifra" data-testid="total-pago">
                {f.precio(total)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt>Saldo actual</dt>
              <dd className="cifra">{f.precio(saldo)}</dd>
            </div>
            {alcanza ? (
              <div className="flex justify-between text-tinta-suave">
                <dt>Saldo después del pago</dt>
                <dd className="cifra">{f.precio(saldo - total)}</dd>
              </div>
            ) : null}
          </dl>
          {!alcanza ? (
            <Aviso tipo="error">
              Tu saldo no alcanza. <Link href="/cliente/monedero" className="font-semibold underline">Recarga el monedero</Link> y vuelve a intentarlo.
            </Aviso>
          ) : null}
          <FormularioPago reservas={pagables.map((r) => r.codigo)} alcanza={alcanza} />
        </Tarjeta>
      )}
    </div>
  );
}
