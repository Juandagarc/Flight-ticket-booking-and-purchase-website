import type { Metadata } from "next";
import Link from "next/link";

import { FormularioBusqueda } from "@/components/FormularioBusqueda";
import { TarjetaNoticia } from "@/components/TarjetaNoticia";
import { Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { obtenerCiudades, obtenerNoticias } from "@/lib/datos";
import * as f from "@/lib/formato";
import { exigirSesion } from "@/lib/sesion";
import type { Actividad, UsuarioDetalle } from "@/lib/tipos";

export const metadata: Metadata = { title: "Mi cuenta" };

function describir(a: Actividad) {
  const partes = [];
  if (a.origen || a.destino) partes.push(`${a.origen ?? "Cualquier origen"} → ${a.destino ?? "cualquier destino"}`);
  if (a.fecha_desde || a.fecha_hasta) partes.push(`${a.fecha_desde ?? "…"} a ${a.fecha_hasta ?? "…"}`);
  if (a.precio_min || a.precio_max)
    partes.push(`${a.precio_min ? f.precio(a.precio_min) : "$0"} – ${a.precio_max ? f.precio(a.precio_max) : "sin tope"}`);
  if (a.pasajeros) partes.push(`${a.pasajeros} pas.`);
  return partes.join(" · ") || "Todos los vuelos";
}

function enlace(a: Actividad) {
  const q = new URLSearchParams();
  for (const k of ["origen", "destino", "fecha_desde", "fecha_hasta", "precio_min", "precio_max"] as const) {
    if (a[k]) q.set(k, String(a[k]));
  }
  if (a.pasajeros) q.set("pasajeros", String(a.pasajeros));
  return `/vuelos?${q}`;
}

/** Inicio del cliente después de iniciar sesión (HU-002): búsqueda, búsquedas recientes y noticias. */
export default async function PanelCliente() {
  const sesion = await exigirSesion("CLIENTE");
  const [yo, actividad, ciudades, { noticias }] = await Promise.all([
    api<UsuarioDetalle>("/auth/me", { token: sesion.token }),
    api<Actividad[]>("/usuarios/me/actividad", { token: sesion.token, consulta: { limite: 5 } }),
    obtenerCiudades(),
    obtenerNoticias(3),
  ]);

  return (
    <div className="flex flex-col gap-8">
      <Encabezado titulo={`Hola, ${yo.perfil?.nombres.split(" ")[0] ?? yo.nombre_usuario}`} bajada="¿A dónde vamos?" />
      <Tarjeta>
        <FormularioBusqueda ciudades={ciudades} completo={false} />
      </Tarjeta>
      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Tarjeta>
          <h2 className="mb-3 font-semibold">Búsquedas recientes</h2>
          {actividad.length === 0 ? (
            <p className="text-sm text-tinta-suave">Tus búsquedas aparecerán aquí.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-linea" data-testid="busquedas-recientes">
              {actividad.map((a) => (
                <li key={a.fecha} className="py-2.5">
                  <Link href={enlace(a)} className="text-sm font-medium hover:text-cielo">
                    {describir(a)}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>
        <section>
          <h2 className="mb-3 font-semibold">Novedades</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {noticias.slice(0, 2).map((n) => (
              <TarjetaNoticia key={n.id} noticia={n} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
