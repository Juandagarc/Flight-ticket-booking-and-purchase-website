import type { ComponentProps, ReactNode } from "react";

export function cx(...clases: Array<string | false | null | undefined>) {
  return clases.filter(Boolean).join(" ");
}

const baseControl =
  "w-full rounded-lg border bg-superficie px-3 py-2.5 text-[15px] text-tinta outline-none transition focus:border-cielo focus:ring-2 focus:ring-cielo/20 disabled:bg-fondo disabled:text-tinta-suave";

interface CampoProps {
  etiqueta: string;
  nombre: string;
  error?: string;
  ayuda?: string;
  children?: ReactNode;
}

function Envoltura({ etiqueta, nombre, error, ayuda, children }: CampoProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={nombre} className="text-sm font-medium text-tinta">
        {etiqueta}
      </label>
      {children}
      {error ? (
        <p id={`${nombre}-error`} role="alert" className="text-sm text-error">
          {error}
        </p>
      ) : ayuda ? (
        <p className="text-xs text-tinta-suave">{ayuda}</p>
      ) : null}
    </div>
  );
}

export function Campo({
  etiqueta,
  nombre,
  error,
  ayuda,
  ...props
}: CampoProps & Omit<ComponentProps<"input">, "name" | "id">) {
  return (
    <Envoltura etiqueta={etiqueta} nombre={nombre} error={error} ayuda={ayuda}>
      <input
        id={nombre}
        name={nombre}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${nombre}-error` : undefined}
        className={cx(baseControl, error ? "border-error" : "border-linea")}
        {...props}
      />
    </Envoltura>
  );
}

export function Seleccion({
  etiqueta,
  nombre,
  error,
  ayuda,
  children,
  ...props
}: CampoProps & Omit<ComponentProps<"select">, "name" | "id">) {
  return (
    <Envoltura etiqueta={etiqueta} nombre={nombre} error={error} ayuda={ayuda}>
      <select
        id={nombre}
        name={nombre}
        aria-invalid={error ? true : undefined}
        className={cx(baseControl, "appearance-none", error ? "border-error" : "border-linea")}
        {...props}
      >
        {children}
      </select>
    </Envoltura>
  );
}

type Variante = "primario" | "secundario" | "fantasma";

const variantes: Record<Variante, string> = {
  primario: "bg-cielo text-white hover:bg-cielo-oscuro",
  secundario: "border border-linea bg-superficie text-tinta hover:border-tinta-suave",
  fantasma: "text-cielo hover:bg-cielo-claro",
};

export function botonClases(variante: Variante = "primario", extra?: string) {
  return cx(
    "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-[15px] font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
    variantes[variante],
    extra,
  );
}

export function Boton({
  variante = "primario",
  className,
  ...props
}: ComponentProps<"button"> & { variante?: Variante }) {
  return <button className={botonClases(variante, className)} {...props} />;
}

export function Aviso({ tipo = "info", children }: { tipo?: "info" | "exito" | "error"; children: ReactNode }) {
  const estilos = {
    info: "border-cielo/30 bg-cielo-claro text-cielo-oscuro",
    exito: "border-exito/30 bg-exito-claro text-exito",
    error: "border-error/30 bg-error-claro text-error",
  }[tipo];
  return (
    <div role={tipo === "error" ? "alert" : "status"} className={cx("rounded-lg border px-4 py-3 text-sm", estilos)}>
      {children}
    </div>
  );
}

export function Tarjeta({ className, ...props }: ComponentProps<"section">) {
  return <section className={cx("rounded-2xl border border-linea bg-superficie p-6", className)} {...props} />;
}

export function Encabezado({ titulo, bajada, children }: { titulo: string; bajada?: string; children?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{titulo}</h1>
        {bajada ? <p className="mt-1 text-tinta-suave">{bajada}</p> : null}
      </div>
      {children}
    </div>
  );
}
