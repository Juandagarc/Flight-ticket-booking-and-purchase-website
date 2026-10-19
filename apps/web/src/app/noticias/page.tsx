import type { Metadata } from "next";
import Link from "next/link";

import { TarjetaNoticia } from "@/components/TarjetaNoticia";
import { Aviso, cx, Encabezado } from "@/components/ui";
import { obtenerNoticias } from "@/lib/datos";

export const metadata: Metadata = { title: "Noticias" };
export const dynamic = "force-dynamic";

const FILTROS = [
  { valor: "", texto: "Todo" },
  { valor: "NUEVO_VUELO", texto: "Nuevos vuelos" },
  { valor: "PROMOCION", texto: "Promociones" },
];

/** HU-009 · Pantalla 06: catálogo público de noticias, sin iniciar sesión (RF-64, RF-65). */
export default async function Noticias({ searchParams }: { searchParams: Promise<{ tipo?: string }> }) {
  const { tipo = "" } = await searchParams;
  const { noticias, error } = await obtenerNoticias(100, tipo || undefined);

  return (
    <div>
      <Encabezado titulo="Noticias y promociones" bajada="Cada vuelo que programamos aparece aquí apenas sale a la venta." />
      <nav aria-label="Filtrar noticias" className="mb-6 flex gap-2">
        {FILTROS.map((fl) => (
          <Link
            key={fl.valor}
            href={fl.valor ? `/noticias?tipo=${fl.valor}` : "/noticias"}
            className={cx(
              "rounded-full border px-4 py-1.5 text-sm font-medium",
              tipo === fl.valor ? "border-tinta bg-tinta text-white" : "border-linea bg-superficie hover:border-tinta-suave",
            )}
          >
            {fl.texto}
          </Link>
        ))}
      </nav>
      {error ? <Aviso tipo="error">{error}</Aviso> : null}
      {!error && noticias.length === 0 ? <Aviso>No hay noticias por ahora.</Aviso> : null}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {noticias.map((n) => (
          <TarjetaNoticia key={n.id} noticia={n} />
        ))}
      </div>
    </div>
  );
}
