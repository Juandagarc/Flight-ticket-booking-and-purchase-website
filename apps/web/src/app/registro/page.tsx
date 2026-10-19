import type { Metadata } from "next";
import Link from "next/link";

import { FormularioRegistro } from "@/components/FormularioRegistro";
import { Tarjeta } from "@/components/ui";

export const metadata: Metadata = { title: "Crear cuenta" };

export default function Registro() {
  return (
    <div className="mx-auto max-w-3xl">
      <Tarjeta className="p-6 sm:p-8">
        <h1 className="text-2xl font-bold">Crear cuenta de cliente</h1>
        <p className="mb-6 mt-1 text-sm text-tinta-suave">
          Con tu cuenta puedes reservar y comprar tiquetes para ti o para otras personas. ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="font-semibold text-cielo hover:underline">
            Inicia sesión
          </Link>
        </p>
        <FormularioRegistro />
      </Tarjeta>
    </div>
  );
}
