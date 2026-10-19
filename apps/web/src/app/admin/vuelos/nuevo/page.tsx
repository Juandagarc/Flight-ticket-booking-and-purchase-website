import type { Metadata } from "next";

import { programarVuelo } from "@/acciones/admin";
import { FormularioVuelo } from "@/components/FormularioVuelo";
import { Encabezado, Tarjeta } from "@/components/ui";
import { obtenerCiudades } from "@/lib/datos";
import { exigirSesion } from "@/lib/sesion";

export const metadata: Metadata = { title: "Programar vuelo" };

/** HU-006 · Pantalla 27: programar vuelo. */
export default async function ProgramarVuelo() {
  await exigirSesion("ADMINISTRADOR");
  const ciudades = await obtenerCiudades();
  return (
    <div className="mx-auto max-w-3xl">
      <Encabezado titulo="Programar vuelo" bajada="Vuelos directos entre capitales o hacia los destinos internacionales." />
      <Tarjeta>
        <FormularioVuelo accion={programarVuelo} ciudades={ciudades} textoBoton="Programar vuelo" />
      </Tarjeta>
    </div>
  );
}
