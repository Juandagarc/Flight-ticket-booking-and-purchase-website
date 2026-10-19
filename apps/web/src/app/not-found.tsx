import Link from "next/link";

import { botonClases } from "@/components/ui";

export default function NoEncontrado() {
  return (
    <div className="mx-auto max-w-md py-16 text-center">
      <p className="text-sm font-semibold text-cielo">404</p>
      <h1 className="mt-2 text-2xl font-bold">No encontramos esta página</h1>
      <p className="mt-2 text-tinta-suave">Puede que el vuelo o la dirección ya no existan.</p>
      <Link href="/" className={botonClases("primario", "mt-6")}>
        Ir al inicio
      </Link>
    </div>
  );
}
