import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { Ruta } from "@/components/TarjetaVuelo";
import { Aviso, botonClases, Tarjeta } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Vuelo } from "@/lib/tipos";

export const metadata: Metadata = { title: "Reservar" };

/**
 * Punto de entrada a la reserva y la compra. En esta iteración garantiza la barrera de acceso
 * (RF-33, RF-34): el visitante va al inicio de sesión y root o administrador no entran.
 * El flujo de reserva y compra se construye en la iteración 2 (HU-010 y HU-011).
 */
export default async function Reservar({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params;
  const sesion = await exigirSesion();
  try {
    await api("/reservas/acceso", { token: sesion.token });
  } catch (e) {
    if (e instanceof ApiError && e.estado === 403) redirect("/admin?aviso=sin-compras");
    if (e instanceof ApiError && e.estado === 401) redirect(`/login?next=/reservar/${codigo}`);
    throw e;
  }

  let vuelo: Vuelo;
  try {
    vuelo = await api<Vuelo>(`/vuelos/${encodeURIComponent(codigo)}`);
  } catch (e) {
    if (e instanceof ApiError && e.estado === 404) notFound();
    throw e;
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Tarjeta className="flex flex-col gap-5">
        <div>
          <p className="text-sm text-tinta-suave">
            Vuelo {vuelo.codigo} · {f.fechaCorta(vuelo.salida_local)}
          </p>
          <h1 className="text-2xl font-bold">
            {vuelo.origen.nombre} → {vuelo.destino.nombre}
          </h1>
        </div>
        <Ruta vuelo={vuelo} />
        <Aviso>La reserva y la compra de tiquetes estarán disponibles en la próxima entrega.</Aviso>
        <Link href="/vuelos" className={botonClases("secundario", "self-start")}>
          Volver a la búsqueda
        </Link>
      </Tarjeta>
    </div>
  );
}
