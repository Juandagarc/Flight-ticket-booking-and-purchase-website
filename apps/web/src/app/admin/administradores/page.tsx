import type { Metadata } from "next";

import { FormularioAdministrador } from "@/components/FormularioAdministrador";
import { Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Administrador } from "@/lib/tipos";

export const metadata: Metadata = { title: "Administradores" };

/** HU-005 · Pantalla 38: solo el root crea administradores. */
export default async function Administradores() {
  const sesion = await exigirSesion("ROOT");
  const admins = await api<Administrador[]>("/administradores", { token: sesion.token });
  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <div>
        <Encabezado titulo="Administradores" bajada="Solo el root puede crearlos." />
        <Tarjeta>
          <h2 className="mb-4 text-lg font-semibold">Nuevo administrador</h2>
          <FormularioAdministrador />
        </Tarjeta>
      </div>
      <Tarjeta className="h-fit lg:mt-[4.5rem]">
        <h2 className="mb-3 text-lg font-semibold">Cuentas creadas</h2>
        {admins.length === 0 ? (
          <p className="text-sm text-tinta-suave">Aún no hay administradores.</p>
        ) : (
          <ul className="divide-y divide-linea" data-testid="lista-administradores">
            {admins.map((a) => (
              <li key={a.id} className="flex items-center justify-between py-3 text-sm">
                <span className="font-medium">{a.nombre_usuario}</span>
                <span className="text-tinta-suave">Creado el {f.fechaCorta(a.fecha_creacion.slice(0, 10))}</span>
              </li>
            ))}
          </ul>
        )}
      </Tarjeta>
    </div>
  );
}
