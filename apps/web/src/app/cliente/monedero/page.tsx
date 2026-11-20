import type { Metadata } from "next";

import { quitarTarjeta } from "@/acciones/compras";
import { FormularioSaldo, FormularioTarjeta } from "@/components/FormulariosCompra";
import { botonClases, cx, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Monedero } from "@/lib/tipos";

export const metadata: Metadata = { title: "Monedero" };

/** HU-014 · Pantalla 16: saldo, tarjetas y movimientos del monedero (simulado). */
export default async function PaginaMonedero() {
  const sesion = await exigirSesion("CLIENTE");
  const m = await api<Monedero>("/monedero", { token: sesion.token });

  return (
    <div className="flex flex-col gap-6">
      <Encabezado titulo="Monedero" bajada="Saldo para tus compras. Es un monedero simulado: no se hacen cobros reales." />
      <div className="grid gap-6 lg:grid-cols-[1fr_380px] lg:items-start">
        <div className="flex flex-col gap-6">
          <Tarjeta>
            <p className="text-sm text-tinta-suave">Saldo disponible</p>
            <p className="cifra text-4xl font-bold" data-testid="saldo">
              {f.precio(m.saldo)}
            </p>
          </Tarjeta>
          <Tarjeta>
            <h2 className="mb-3 font-semibold">Movimientos</h2>
            {m.movimientos.length === 0 ? (
              <p className="text-sm text-tinta-suave">Todavía no hay movimientos.</p>
            ) : (
              <ul className="flex flex-col divide-y divide-linea" data-testid="movimientos">
                {m.movimientos.map((x) => (
                  <li key={x.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                    <div>
                      <p className="font-medium">{f.MOVIMIENTO[x.tipo]}</p>
                      <p className="text-xs text-tinta-suave">
                        {f.momento(x.fecha)}
                        {x.descripcion ? ` · ${x.descripcion}` : ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={cx("cifra font-semibold", Number(x.monto) < 0 ? "text-error" : "text-exito")}>
                        {Number(x.monto) > 0 ? "+" : ""}
                        {f.precio(x.monto)}
                      </p>
                      <p className="cifra text-xs text-tinta-suave">Saldo {f.precio(x.saldo_resultante)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Tarjeta>
        </div>
        <div className="flex flex-col gap-6">
          <Tarjeta>
            <h2 className="mb-3 font-semibold">Editar saldo</h2>
            <FormularioSaldo saldo={m.saldo} />
          </Tarjeta>
          <Tarjeta>
            <h2 className="mb-3 font-semibold">Tarjetas</h2>
            {m.tarjetas.length ? (
              <ul className="mb-5 flex flex-col gap-2" data-testid="tarjetas">
                {m.tarjetas.map((t) => (
                  <li key={t.id} className="flex items-center justify-between rounded-lg border border-linea px-3 py-2 text-sm">
                    <span>
                      <span className="font-semibold">{t.franquicia}</span> •••• {t.ultimos_digitos}
                      <span className="block text-xs text-tinta-suave">
                        {t.tipo === "CREDITO" ? "Crédito" : "Débito"} · vence {t.vencimiento}
                      </span>
                    </span>
                    <form action={quitarTarjeta}>
                      <input type="hidden" name="id" value={t.id} />
                      <button className={botonClases("fantasma", "px-2 py-1 text-xs")}>Quitar</button>
                    </form>
                  </li>
                ))}
              </ul>
            ) : null}
            <FormularioTarjeta />
          </Tarjeta>
        </div>
      </div>
    </div>
  );
}
