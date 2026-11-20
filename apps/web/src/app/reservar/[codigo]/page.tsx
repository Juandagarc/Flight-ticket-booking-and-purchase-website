import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { FormularioReserva } from "@/components/FormularioReserva";
import { Ruta } from "@/components/TarjetaVuelo";
import { Aviso, botonClases, Tarjeta } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { UsuarioDetalle, Vuelo } from "@/lib/tipos";

export const metadata: Metadata = { title: "Reservar" };

/**
 * HU-010 y HU-011 · Reserva y compra. Solo el cliente entra (RF-33, RF-34): el visitante va al
 * inicio de sesión y root o administrador son devueltos a su panel.
 */
export default async function Reservar({
  params,
  searchParams,
}: {
  params: Promise<{ codigo: string }>;
  searchParams: Promise<{ pasajeros?: string }>;
}) {
  const { codigo } = await params;
  const { pasajeros } = await searchParams;
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
  const [regresos, yo] = await Promise.all([
    api<Vuelo[]>(`/vuelos/${encodeURIComponent(codigo)}/regresos`),
    api<UsuarioDetalle>("/auth/me", { token: sesion.token }),
  ]);
  const vendible = vuelo.estado === "PROGRAMADO" && vuelo.disponibles.primera + vuelo.disponibles.economica > 0;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Tarjeta className="flex flex-col gap-5">
        <div>
          <p className="text-sm text-tinta-suave">
            Vuelo {vuelo.codigo} · {f.fechaCorta(vuelo.salida_local)} · {vuelo.tipo === "NACIONAL" ? "Nacional" : "Internacional"}
          </p>
          <h1 className="text-2xl font-bold">
            {vuelo.origen.nombre} → {vuelo.destino.nombre}
          </h1>
        </div>
        <Ruta vuelo={vuelo} />
      </Tarjeta>
      {vendible ? (
        <Tarjeta>
          <FormularioReserva
            vuelo={vuelo}
            regresos={regresos}
            perfil={yo.perfil}
            pasajerosIniciales={Math.min(5, Math.max(1, Number(pasajeros) || 1))}
          />
        </Tarjeta>
      ) : (
        <Tarjeta className="flex flex-col gap-4">
          <Aviso tipo="error">Este vuelo ya no está disponible para la venta.</Aviso>
          <Link href="/vuelos" className={botonClases("secundario", "self-start")}>
            Volver a la búsqueda
          </Link>
        </Tarjeta>
      )}
    </div>
  );
}
