"use client";

import { useFormStatus } from "react-dom";

import { Boton } from "./ui";

export function BotonEnviar({ children, pendiente = "Guardando…", className }: { children: React.ReactNode; pendiente?: string; className?: string }) {
  const { pending } = useFormStatus();
  return (
    <Boton type="submit" disabled={pending} className={className}>
      {pending ? pendiente : children}
    </Boton>
  );
}
