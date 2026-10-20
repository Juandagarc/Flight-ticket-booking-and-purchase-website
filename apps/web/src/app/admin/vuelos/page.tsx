import type { Metadata } from "next";
import Link from "next/link";

import { Aviso, botonClases, cx, Encabezado } from "@/components/ui";
import { api } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Vuelo } from "@/lib/tipos";

export const metadata: Metadata = { title: "Gestión de vuelos" };

const ESTADOS: Record<Vuelo["estado"], string> = {
  PROGRAMADO: "bg-cielo-claro text-cielo-oscuro",
  CANCELADO: "bg-error-claro text-error",
  REALIZADO: "bg-fondo text-tinta-suave",
};

/** HU-006 y HU-007 · Pantalla 26: hub de gestión de vuelos. */
export default async function GestionVuelos({
  searchParams,
}: {
  searchParams: Promise<{ programado?: string; editado?: string }>;
}) {
  const sesion = await exigirSesion("ADMINISTRADOR");
  const { programado, editado } = await searchParams;
  const vuelos = await api<Vuelo[]>("/vuelos/gestion", { token: sesion.token });

  return (
    <div>
      <Encabezado titulo="Gestión de vuelos" bajada={`${vuelos.length} vuelos`}>
        <Link href="/admin/vuelos/nuevo" className={botonClases()}>
          Programar vuelo
        </Link>
      </Encabezado>
      {programado ? (
        <div className="mb-4">
          <Aviso tipo="exito">Vuelo {programado} programado y publicado en Noticias.</Aviso>
        </div>
      ) : null}
      {editado ? (
        <div className="mb-4">
          <Aviso tipo="exito">Vuelo {editado} actualizado.</Aviso>
        </div>
      ) : null}
      {vuelos.length === 0 ? (
        <Aviso>Aún no hay vuelos. Programa el primero.</Aviso>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-linea bg-superficie">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead className="border-b border-linea bg-fondo text-xs uppercase tracking-wide text-tinta-suave">
              <tr>
                <th className="px-4 py-3">Código</th>
                <th className="px-4 py-3">Ruta</th>
                <th className="px-4 py-3">Salida (local)</th>
                <th className="px-4 py-3">Llegada (local)</th>
                <th className="px-4 py-3">Duración</th>
                <th className="px-4 py-3 text-right">Primera</th>
                <th className="px-4 py-3 text-right">Económica</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-linea">
              {vuelos.map((v) => (
                <tr key={v.codigo} data-testid={`fila-${v.codigo}`}>
                  <td className="px-4 py-3 font-semibold">{v.codigo}</td>
                  <td className="px-4 py-3">
                    {v.origen.nombre} → {v.destino.nombre}
                    <span className="block text-xs text-tinta-suave">{v.tipo === "NACIONAL" ? "Nacional" : "Internacional"}</span>
                  </td>
                  <td className="cifra whitespace-nowrap px-4 py-3">{f.fechaHora(v.salida_local)}</td>
                  <td className="cifra whitespace-nowrap px-4 py-3">{f.fechaHora(v.llegada_local)}</td>
                  <td className="whitespace-nowrap px-4 py-3">{f.duracion(v.duracion_min)}</td>
                  <td className="cifra whitespace-nowrap px-4 py-3 text-right">{f.precio(v.tarifas.primera)}</td>
                  <td className="cifra whitespace-nowrap px-4 py-3 text-right">{f.precio(v.tarifas.economica)}</td>
                  <td className="px-4 py-3">
                    <span className={cx("rounded-full px-2 py-0.5 text-xs font-semibold", ESTADOS[v.estado])}>
                      {v.estado.toLowerCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {v.editable ? (
                      <Link href={`/admin/vuelos/${v.codigo}`} className="font-semibold text-cielo hover:underline">
                        Editar
                      </Link>
                    ) : (
                      <span className="text-xs text-tinta-suave" title="Ya ocurrió, no está programado o tiene tiquetes vendidos">
                        No editable
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
