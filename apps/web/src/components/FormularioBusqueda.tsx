import type { Ciudad } from "@/lib/tipos";

import { Campo, Seleccion } from "./ui";

export interface Criterios {
  origen?: string;
  destino?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  precio_min?: string;
  precio_max?: string;
  pasajeros?: string;
}

function OpcionesCiudades({ ciudades }: { ciudades: Ciudad[] }) {
  const nacionales = ciudades.filter((c) => c.es_capital_nacional);
  const internacionales = ciudades.filter((c) => !c.es_capital_nacional);
  return (
    <>
      <option value="">Cualquiera</option>
      <optgroup label="Colombia">
        {nacionales.map((c) => (
          <option key={c.codigo} value={c.codigo}>
            {c.nombre} ({c.codigo})
          </option>
        ))}
      </optgroup>
      <optgroup label="Internacional">
        {internacionales.map((c) => (
          <option key={c.codigo} value={c.codigo}>
            {c.nombre} ({c.codigo})
          </option>
        ))}
      </optgroup>
    </>
  );
}

/** HU-008 · Pantalla 02: búsqueda por origen, destino, fechas, precios y pasajeros. */
export function FormularioBusqueda({
  ciudades,
  criterios = {},
  completo = true,
  errores = {},
}: {
  ciudades: Ciudad[];
  criterios?: Criterios;
  completo?: boolean;
  errores?: Record<string, string>;
}) {
  return (
    <form action="/vuelos" method="get" role="search" aria-label="Buscar vuelos" className="grid gap-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Seleccion etiqueta="Origen" nombre="origen" defaultValue={criterios.origen ?? ""}>
          <OpcionesCiudades ciudades={ciudades} />
        </Seleccion>
        <Seleccion etiqueta="Destino" nombre="destino" defaultValue={criterios.destino ?? ""}>
          <OpcionesCiudades ciudades={ciudades} />
        </Seleccion>
        <Campo etiqueta="Desde" nombre="fecha_desde" type="date" defaultValue={criterios.fecha_desde} />
        <Campo
          etiqueta="Hasta"
          nombre="fecha_hasta"
          type="date"
          defaultValue={criterios.fecha_hasta}
          error={errores.fecha_hasta}
        />
        <Seleccion etiqueta="Pasajeros" nombre="pasajeros" defaultValue={criterios.pasajeros ?? "1"}>
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n} {n === 1 ? "pasajero" : "pasajeros"}
            </option>
          ))}
        </Seleccion>
      </div>
      {completo ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Campo
            etiqueta="Precio mínimo (COP)"
            nombre="precio_min"
            type="number"
            min={0}
            step={1000}
            inputMode="numeric"
            defaultValue={criterios.precio_min}
          />
          <Campo
            etiqueta="Precio máximo (COP)"
            nombre="precio_max"
            type="number"
            min={0}
            step={1000}
            inputMode="numeric"
            defaultValue={criterios.precio_max}
            error={errores.precio_max}
          />
          <div className="flex items-end lg:col-start-5">
            <button type="submit" className="w-full rounded-lg bg-cielo px-4 py-2.5 font-semibold text-white hover:bg-cielo-oscuro">
              Buscar vuelos
            </button>
          </div>
        </div>
      ) : (
        <div className="flex justify-end">
          <button type="submit" className="w-full rounded-lg bg-cielo px-6 py-2.5 font-semibold text-white hover:bg-cielo-oscuro sm:w-auto">
            Buscar vuelos
          </button>
        </div>
      )}
    </form>
  );
}
