import type { Metadata } from "next";
import Link from "next/link";

import { moverEnCarrito } from "@/acciones/compras";
import { TarjetaReserva } from "@/components/Reservas";
import { botonClases, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Carrito } from "@/lib/tipos";

export const metadata: Metadata = { title: "Carrito" };

/** HU-012 · Pantalla 14: carrito con varias reservas, subtotales y total. */
export default async function PaginaCarrito() {
  const sesion = await exigirSesion("CLIENTE");
  const carrito = await api<Carrito>("/carrito", { token: sesion.token });

  return (
    <div className="flex flex-col gap-6">
      <Encabezado titulo="Carrito" bajada="Reservas pendientes de pago. Cada una se libera a las 24 horas si no se paga." />
      {carrito.reservas.length === 0 ? (
        <Tarjeta className="flex flex-col items-start gap-4">
          <p className="text-tinta-suave">Tu carrito está vacío.</p>
          <Link href="/vuelos" className={botonClases()}>
            Buscar vuelos
          </Link>
        </Tarjeta>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_320px] lg:items-start">
          <div className="flex flex-col gap-4">
            {carrito.reservas.map((r) => (
              <TarjetaReserva
                key={r.codigo}
                reserva={r}
                acciones={
                  <>
                    <form action={moverEnCarrito}>
                      <input type="hidden" name="codigo" value={r.codigo} />
                      <input type="hidden" name="dentro" value="0" />
                      <button className={botonClases("fantasma", "text-sm")}>Quitar del carrito</button>
                    </form>
                    <Link href={`/cliente/pago?reservas=${r.codigo}`} className={botonClases("secundario", "text-sm")}>
                      Pagar solo esta
                    </Link>
                  </>
                }
              />
            ))}
          </div>
          <Tarjeta className="flex flex-col gap-4 lg:sticky lg:top-6">
            <dl className="flex flex-col gap-2 text-sm">
              {carrito.reservas.map((r) => (
                <div key={r.codigo} className="flex justify-between">
                  <dt>{r.codigo}</dt>
                  <dd className="cifra">{f.precio(r.total)}</dd>
                </div>
              ))}
              <div className="flex justify-between border-t border-linea pt-2 text-base font-bold">
                <dt>Total</dt>
                <dd className="cifra" data-testid="total-carrito">
                  {f.precio(carrito.total)}
                </dd>
              </div>
              <div className="flex justify-between text-tinta-suave">
                <dt>Saldo del monedero</dt>
                <dd className="cifra">{f.precio(carrito.saldo)}</dd>
              </div>
            </dl>
            <Link href="/cliente/pago" className={botonClases("primario", "w-full")}>
              Pagar todo
            </Link>
          </Tarjeta>
        </div>
      )}
    </div>
  );
}
