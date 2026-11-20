import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { moverEnCarrito } from "@/acciones/compras";
import { FormularioCancelar } from "@/components/FormulariosCompra";
import { EstadoReserva, LineaTramo } from "@/components/Reservas";
import { Aviso, botonClases, Tarjeta } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { ReservaDetalle } from "@/lib/tipos";

export const metadata: Metadata = { title: "Detalle de la reserva" };

/** HU-017 · Pantalla 18: detalle de una reserva o compra, con pago y cancelación (HU-015, HU-016). */
export default async function DetalleReserva({
  params,
  searchParams,
}: {
  params: Promise<{ codigo: string }>;
  searchParams: Promise<{ nueva?: string; comprada?: string; cancelada?: string }>;
}) {
  const { codigo } = await params;
  const aviso = await searchParams;
  const sesion = await exigirSesion("CLIENTE");
  let r: ReservaDetalle;
  try {
    r = await api<ReservaDetalle>(`/reservas/${encodeURIComponent(codigo)}`, { token: sesion.token });
  } catch (e) {
    if (e instanceof ApiError && e.estado === 404) notFound();
    throw e;
  }
  const compra = r.estado === "PAGADA";

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      {aviso.nueva && r.estado === "RESERVADA" ? (
        <Aviso tipo="exito">Reserva creada y agregada al carrito. Tienes hasta el {f.momento(r.fecha_expiracion!)} para pagarla.</Aviso>
      ) : null}
      {aviso.comprada && compra ? (
        <Aviso tipo="exito">Compra realizada. Enviamos el código {r.codigo} al correo de cada viajero.</Aviso>
      ) : null}
      {aviso.cancelada && r.estado === "CANCELADA" ? (
        <Aviso tipo="exito">
          {r.reembolso ? `Compra cancelada. Devolvimos ${f.precio(r.reembolso)} a tu monedero.` : "Reserva cancelada. Las sillas quedaron libres."}
        </Aviso>
      ) : null}

      <Tarjeta className="flex flex-col gap-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm text-tinta-suave">Código de reserva</p>
            <h1 className="cifra text-3xl font-bold tracking-wider" data-testid="codigo-reserva">
              {r.codigo}
            </h1>
          </div>
          <div className="flex flex-col items-end gap-1">
            <EstadoReserva estado={r.estado} />
            <p className="cifra text-xl font-bold">{f.precio(r.total)}</p>
          </div>
        </div>
        <div className="flex flex-col gap-3">
          {r.tramos.map((t) => (
            <LineaTramo key={t.vuelo_codigo} tramo={t} />
          ))}
        </div>
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-tinta-suave">Creada</dt>
            <dd>{f.momento(r.fecha_creacion)}</dd>
          </div>
          {r.fecha_expiracion ? (
            <div>
              <dt className="text-xs text-tinta-suave">Vence si no se paga</dt>
              <dd>{f.momento(r.fecha_expiracion)}</dd>
            </div>
          ) : null}
          {r.pago_fecha ? (
            <div>
              <dt className="text-xs text-tinta-suave">Pagada</dt>
              <dd>{f.momento(r.pago_fecha)}</dd>
            </div>
          ) : null}
          {r.limite_cancelacion ? (
            <div>
              <dt className="text-xs text-tinta-suave">Se puede cancelar hasta</dt>
              <dd>{f.momento(r.limite_cancelacion)}</dd>
            </div>
          ) : null}
          {r.reembolso && r.reembolso_fecha ? (
            <div>
              <dt className="text-xs text-tinta-suave">Reembolso</dt>
              <dd>
                {f.precio(r.reembolso)} · {f.momento(r.reembolso_fecha)}
              </dd>
            </div>
          ) : null}
        </dl>
      </Tarjeta>

      <Tarjeta>
        <h2 className="mb-4 font-semibold">Tiquetes</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="text-xs text-tinta-suave">
              <tr>
                <th className="py-2 pr-3 font-medium">Viajero</th>
                <th className="py-2 pr-3 font-medium">Vuelo</th>
                <th className="py-2 pr-3 font-medium">Silla</th>
                <th className="py-2 pr-3 font-medium">Clase</th>
                <th className="py-2 pr-3 font-medium">Check-in</th>
                <th className="py-2 text-right font-medium">Precio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-linea">
              {r.tiquetes.map((t) => (
                <tr key={t.id} data-testid="tiquete">
                  <td className="py-2.5 pr-3">
                    <span className="block font-medium">{t.pasajero_nombre}</span>
                    <span className="text-xs text-tinta-suave">{t.pasajero_documento}</span>
                  </td>
                  <td className="py-2.5 pr-3">
                    <span className="block">
                      {t.origen.codigo} → {t.destino.codigo}
                    </span>
                    <span className="text-xs text-tinta-suave">{f.fechaHora(t.salida_local)}</span>
                  </td>
                  <td className="cifra py-2.5 pr-3">
                    {t.silla} <span className="text-xs text-tinta-suave">· {f.POSICION[t.posicion]}</span>
                  </td>
                  <td className="py-2.5 pr-3">{f.CLASE[t.clase]}</td>
                  <td className="py-2.5 pr-3">{t.estado === "CANCELADO" ? "—" : t.checkin === "REALIZADO" ? "Realizado" : "Pendiente"}</td>
                  <td className="cifra py-2.5 text-right">{f.precio(t.precio)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Tarjeta>

      {r.puede_pagar ? (
        <Tarjeta className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm">Esta reserva aún no está pagada.</p>
          <div className="flex flex-wrap gap-2">
            {!r.en_carrito ? (
              <form action={moverEnCarrito}>
                <input type="hidden" name="codigo" value={r.codigo} />
                <input type="hidden" name="dentro" value="1" />
                <button className={botonClases("secundario")}>Volver al carrito</button>
              </form>
            ) : null}
            <Link href={`/cliente/pago?reservas=${r.codigo}`} className={botonClases()}>
              Pagar
            </Link>
          </div>
        </Tarjeta>
      ) : null}

      {r.puede_cancelar ? (
        <Tarjeta>
          <h2 className="mb-1 font-semibold">{compra ? "Cancelar compra" : "Cancelar reserva"}</h2>
          <p className="mb-4 text-sm text-tinta-suave">
            {compra
              ? "Las compras se cancelan hasta una hora antes en vuelos nacionales y tres horas antes en internacionales, con devolución del 100 % al monedero."
              : "Puedes cancelar una reserva mientras esté vigente."}
          </p>
          <FormularioCancelar codigo={r.codigo} compra={compra} />
        </Tarjeta>
      ) : compra ? (
        <Aviso>El plazo para cancelar esta compra ya pasó.</Aviso>
      ) : null}

      <Link href="/cliente/reservas" className={botonClases("fantasma", "self-start")}>
        ← Mis reservas
      </Link>
    </div>
  );
}
