import Link from "next/link";

import * as f from "@/lib/formato";
import type { Noticia } from "@/lib/tipos";

export function TarjetaNoticia({ noticia }: { noticia: Noticia }) {
  const promo = noticia.tipo === "PROMOCION";
  return (
    <article data-testid="noticia" className="group overflow-hidden rounded-2xl border border-linea bg-superficie">
      <div className="relative aspect-[16/9] overflow-hidden bg-cielo-claro">
        {/* eslint-disable-next-line @next/next/no-img-element -- la imagen puede venir de cualquier origen */}
        <img
          src={noticia.imagen_url}
          alt={`${noticia.origen.nombre} a ${noticia.destino.nombre}`}
          className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
        />
        <span
          className={`absolute left-3 top-3 rounded-full px-2.5 py-1 text-xs font-semibold ${
            promo ? "bg-atardecer text-white" : "bg-superficie/95 text-tinta"
          }`}
        >
          {promo ? "Promoción" : "Nuevo vuelo"}
        </span>
      </div>
      <div className="flex flex-col gap-2 p-4">
        <h3 className="font-semibold leading-snug">{noticia.titulo}</h3>
        <p className="text-sm text-tinta-suave">
          {noticia.origen.nombre} → {noticia.destino.nombre}
        </p>
        <p className="text-sm text-tinta-suave">{f.fechaHora(noticia.salida_local)}</p>
        <div className="mt-1 flex items-end justify-between">
          <p>
            <span className="block text-xs text-tinta-suave">{promo ? "Precio de promoción" : "Desde"}</span>
            <span className="cifra text-lg font-bold text-tinta" data-testid="precio-noticia">
              {f.precio(noticia.precio_unitario)}
            </span>
          </p>
          <Link
            href={`/vuelos?origen=${noticia.origen.codigo}&destino=${noticia.destino.codigo}`}
            className="text-sm font-semibold text-cielo hover:underline"
          >
            Ver vuelo
          </Link>
        </div>
      </div>
    </article>
  );
}
