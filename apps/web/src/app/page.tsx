import Link from "next/link";

import { FormularioBusqueda } from "@/components/FormularioBusqueda";
import { TarjetaNoticia } from "@/components/TarjetaNoticia";
import { Aviso } from "@/components/ui";
import { obtenerCiudades, obtenerNoticias } from "@/lib/datos";
import * as f from "@/lib/formato";

export const dynamic = "force-dynamic";

/** Las imágenes generadas traen el nombre del destino; en el mosaico ya va en el pie. */
const sinTexto = (url: string) => (url.startsWith("/destinos/") ? `${url}?texto=0` : url);

/** Pantalla 01 · Inicio y navegación principal con imágenes de los vuelos programados (RF-10, RNF-06). */
export default async function Inicio() {
  const [ciudades, { noticias, error }] = await Promise.all([obtenerCiudades(), obtenerNoticias(9)]);
  const destacados = noticias.filter((n) => n.tipo === "NUEVO_VUELO").slice(0, 4);

  return (
    <div className="flex flex-col gap-10">
      <section className="overflow-hidden rounded-3xl bg-tinta text-white">
        <div className="grid gap-8 p-6 sm:p-10 lg:grid-cols-[1.1fr_1fr] lg:items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-sky-300">Vuelos directos</p>
            <h1 className="mt-2 text-3xl font-bold leading-tight sm:text-5xl">
              Las 32 capitales de Colombia y cinco destinos en el mundo.
            </h1>
            <p className="mt-4 max-w-lg text-slate-300">
              Busca tu vuelo sin registrarte. Para reservar o comprar solo necesitas una cuenta.
            </p>
          </div>
          {destacados.length > 0 ? (
            <ul className="grid grid-cols-2 gap-3" aria-label="Vuelos programados">
              {destacados.map((n) => (
                <li key={n.id} className="relative aspect-[4/3] overflow-hidden rounded-xl">
                  {/* eslint-disable-next-line @next/next/no-img-element -- imagen alusiva del vuelo */}
                  <img src={sinTexto(n.imagen_url)} alt="" className="h-full w-full object-cover" />
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 to-transparent p-3">
                    <p className="text-sm font-semibold">
                      {n.origen.nombre} → {n.destino.nombre}
                    </p>
                    <p className="cifra text-xs text-slate-200">
                      {f.fechaCorta(n.salida_local)} · desde {f.precio(n.precio_unitario)}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </section>

      <section className="-mt-4 rounded-2xl border border-linea bg-superficie p-5 shadow-sm sm:p-6">
        <FormularioBusqueda ciudades={ciudades} completo={false} />
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between">
          <h2 className="text-xl font-bold">Noticias y promociones</h2>
          <Link href="/noticias" className="text-sm font-semibold text-cielo hover:underline">
            Ver todas
          </Link>
        </div>
        {error ? <Aviso tipo="error">{error}</Aviso> : null}
        {!error && noticias.length === 0 ? (
          <Aviso>Todavía no hay vuelos programados. Vuelve pronto.</Aviso>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {noticias.slice(0, 6).map((n) => (
              <TarjetaNoticia key={n.id} noticia={n} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
