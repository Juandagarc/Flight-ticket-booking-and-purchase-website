import type { Metadata } from "next";
import Link from "next/link";

import { FormularioLogin } from "@/components/FormularioLogin";
import { Aviso, Tarjeta } from "@/components/ui";

export const metadata: Metadata = { title: "Iniciar sesión" };

/** HU-002 · Pantalla 35: inicio de sesión de cliente, administrador y root. */
export default async function Login({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; registrado?: string; usuario?: string }>;
}) {
  const { next, registrado, usuario } = await searchParams;
  return (
    <div className="mx-auto max-w-md">
      <Tarjeta className="p-8">
        <h1 className="text-2xl font-bold">Iniciar sesión</h1>
        <p className="mb-6 mt-1 text-sm text-tinta-suave">Ingresa con tu usuario y contraseña.</p>
        {registrado ? (
          <div className="mb-4">
            <Aviso tipo="exito">Tu cuenta quedó creada. Inicia sesión con tus credenciales.</Aviso>
          </div>
        ) : null}
        {next?.startsWith("/reservar") ? (
          <div className="mb-4">
            <Aviso>Para reservar o comprar necesitas una cuenta de cliente.</Aviso>
          </div>
        ) : null}
        <FormularioLogin next={next} usuario={usuario} />
        <p className="mt-6 text-center text-sm text-tinta-suave">
          ¿No tienes cuenta?{" "}
          <Link href="/registro" className="font-semibold text-cielo hover:underline">
            Regístrate
          </Link>
        </p>
      </Tarjeta>
    </div>
  );
}
