import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { editarVuelo } from "@/acciones/admin";
import { FormularioVuelo } from "@/components/FormularioVuelo";
import { Aviso, botonClases, Encabezado, Tarjeta } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { obtenerCiudades } from "@/lib/datos";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Vuelo } from "@/lib/tipos";

export const metadata: Metadata = { title: "Editar vuelo" };

/** HU-007 · Pantalla 28: editar fecha, hora, ruta o tarifas de un vuelo programado. */
export default async function EditarVuelo({ params }: { params: Promise<{ codigo: string }> }) {
  await exigirSesion("ADMINISTRADOR");
  const { codigo } = await params;
  let vuelo: Vuelo;
  try {
    vuelo = await api<Vuelo>(`/vuelos/${encodeURIComponent(codigo)}`);
  } catch (e) {
    if (e instanceof ApiError && e.estado === 404) notFound();
    throw e;
  }
  const ciudades = await obtenerCiudades();
  const [fecha, horaCompleta] = vuelo.salida_local.split("T");

  return (
    <div className="mx-auto max-w-3xl">
      <Encabezado
        titulo={`Editar vuelo ${vuelo.codigo}`}
        bajada={`${vuelo.origen.nombre} → ${vuelo.destino.nombre} · ${f.fechaHora(vuelo.salida_local)} · ${f.duracion(vuelo.duracion_min)}`}
      />
      {vuelo.editable ? (
        <Tarjeta>
          <FormularioVuelo
            accion={editarVuelo.bind(null, vuelo.codigo)}
            ciudades={ciudades}
            textoBoton="Guardar cambios"
            inicial={{
              origen: vuelo.origen.codigo,
              destino: vuelo.destino.codigo,
              fecha_salida: fecha,
              hora_salida: horaCompleta.slice(0, 5),
              tarifa_primera: String(Math.round(Number(vuelo.tarifas.primera))),
              tarifa_economica: String(Math.round(Number(vuelo.tarifas.economica))),
              imagen_url: vuelo.imagen_url.startsWith("/destinos/") ? "" : vuelo.imagen_url,
            }}
          />
        </Tarjeta>
      ) : (
        <div className="flex flex-col gap-4">
          <Aviso tipo="error">
            Este vuelo no se puede editar: ya ocurrió, no está programado o tiene tiquetes vendidos.
          </Aviso>
          <Link href="/admin/vuelos" className={botonClases("secundario", "self-start")}>
            Volver a la gestión de vuelos
          </Link>
        </div>
      )}
    </div>
  );
}
