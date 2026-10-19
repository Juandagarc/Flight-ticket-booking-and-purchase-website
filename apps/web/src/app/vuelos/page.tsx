import type { Metadata } from "next";

import { FormularioBusqueda, type Criterios } from "@/components/FormularioBusqueda";
import { TarjetaVuelo } from "@/components/TarjetaVuelo";
import { Aviso, Encabezado } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { obtenerCiudades } from "@/lib/datos";
import { obtenerSesion } from "@/lib/sesion";
import type { ResultadoBusqueda } from "@/lib/tipos";

export const metadata: Metadata = { title: "Buscar vuelos" };

const CLAVES = ["origen", "destino", "fecha_desde", "fecha_hasta", "precio_min", "precio_max", "pasajeros"] as const;

/** HU-008 · Pantallas 02 y 03: búsqueda y resultados. Pública; la sesión del cliente registra la búsqueda. */
export default async function BuscarVuelos({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const criterios: Criterios = {};
  for (const k of CLAVES) {
    const v = params[k];
    if (typeof v === "string" && v) criterios[k] = v;
  }
  const buscando = Object.keys(criterios).length > 0;

  const [ciudades, sesion] = await Promise.all([obtenerCiudades(), obtenerSesion()]);
  let resultado: ResultadoBusqueda | null = null;
  let error: ApiError | null = null;
  try {
    resultado = await api<ResultadoBusqueda>("/vuelos/buscar", {
      consulta: { ...criterios },
      token: sesion?.token,
    });
  } catch (e) {
    if (!(e instanceof ApiError)) throw e;
    error = e;
  }

  return (
    <div>
      <Encabezado titulo="Buscar vuelos" bajada="Combina los filtros que quieras: todos son opcionales." />
      <section className="mb-8 rounded-2xl border border-linea bg-superficie p-5 sm:p-6">
        <FormularioBusqueda ciudades={ciudades} criterios={criterios} errores={error?.campos} />
      </section>

      {error ? <Aviso tipo="error">{error.message}</Aviso> : null}

      {resultado ? (
        <section aria-live="polite">
          <h2 className="mb-4 text-lg font-semibold" data-testid="total-resultados">
            {resultado.total === 0
              ? "No encontramos vuelos con esos criterios"
              : `${resultado.total} ${resultado.total === 1 ? "vuelo disponible" : "vuelos disponibles"}${
                  buscando ? "" : " · todos los próximos vuelos"
                }`}
          </h2>
          {resultado.total === 0 ? (
            <p className="text-tinta-suave">Prueba con otras fechas o quita algún filtro.</p>
          ) : (
            <div className="flex flex-col gap-4">
              {resultado.vuelos.map((v) => (
                <TarjetaVuelo key={v.codigo} vuelo={v} pasajeros={Number(criterios.pasajeros) || undefined} />
              ))}
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
