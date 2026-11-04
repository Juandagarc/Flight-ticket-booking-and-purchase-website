import type { Metadata } from "next";
import Link from "next/link";

import { TarjetaReserva } from "@/components/Reservas";
import { Aviso, botonClases, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { exigirSesion } from "@/lib/sesion";
import type { ReservaResumen } from "@/lib/tipos";

export const metadata: Metadata = { title: "Mis reservas" };

/** HU-017 · Pantalla 17: histórico de reservas y compras en todos sus estados. */
export default async function PaginaReservas({ searchParams }: { searchParams: Promise<{ pagadas?: string }> }) {
  const { pagadas } = await searchParams;
  const sesion = await exigirSesion("CLIENTE");
  const reservas = await api<ReservaResumen[]>("/reservas", { token: sesion.token });

  return (
    <div className="flex flex-col gap-6">
      <Encabezado titulo="Mis reservas" bajada="Reservas y compras, de la más reciente a la más antigua." />
      {pagadas ? (
        <Aviso tipo="exito">
          Compra realizada. Enviamos el código de reserva al correo de cada viajero ({pagadas.split(",").join(", ")}).
        </Aviso>
      ) : null}
      {reservas.length === 0 ? (
        <Tarjeta className="flex flex-col items-start gap-4">
          <p className="text-tinta-suave">Aún no tienes reservas.</p>
          <Link href="/vuelos" className={botonClases()}>
            Buscar vuelos
          </Link>
        </Tarjeta>
      ) : (
        <div className="flex flex-col gap-4">
          {reservas.map((r) => (
            <TarjetaReserva
              key={r.codigo}
              reserva={r}
              acciones={
                <Link href={`/cliente/reservas/${r.codigo}`} className={botonClases("secundario", "text-sm")}>
                  Ver detalle
                </Link>
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
