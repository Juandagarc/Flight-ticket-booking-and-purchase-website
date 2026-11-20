"use client";

import { useActionState } from "react";

import { ajustarSaldo, cancelar, guardarTarjeta, pagar } from "@/acciones/compras";
import type { EstadoFormulario } from "@/lib/tipos";

import { BotonEnviar } from "./BotonEnviar";
import { Aviso, Campo, Seleccion } from "./ui";

function Mensaje({ estado }: { estado: EstadoFormulario }) {
  if (!estado.mensaje) return null;
  return <Aviso tipo={estado.ok ? "exito" : "error"}>{estado.mensaje}</Aviso>;
}

/** HU-013 · Pantalla 15: confirma el pago con el saldo del monedero. */
export function FormularioPago({ reservas, alcanza }: { reservas: string[]; alcanza: boolean }) {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(pagar, {});
  return (
    <form action={accion} className="flex flex-col gap-3">
      <input type="hidden" name="reservas" value={reservas.join(",")} />
      <Mensaje estado={estado} />
      <BotonEnviar pendiente="Pagando…" className="sm:self-end">
        {alcanza ? "Pagar con el monedero" : "Intentar pagar"}
      </BotonEnviar>
    </form>
  );
}

/** HU-015 y HU-016: cancelación con confirmación. */
export function FormularioCancelar({ codigo, compra }: { codigo: string; compra: boolean }) {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(cancelar, {});
  return (
    <form action={accion} className="flex flex-col gap-3">
      <input type="hidden" name="codigo" value={codigo} />
      <Mensaje estado={estado} />
      <label className="flex items-start gap-2 text-sm">
        <input type="checkbox" name="confirmo" required className="mt-1" />
        <span>
          {compra
            ? "Entiendo que se cancelan todos los tiquetes de esta compra y el valor vuelve completo a mi monedero."
            : "Entiendo que se liberan las sillas de esta reserva."}
        </span>
      </label>
      <BotonEnviar pendiente="Cancelando…" className="bg-error hover:bg-error/90 sm:self-end">
        {compra ? "Cancelar compra" : "Cancelar reserva"}
      </BotonEnviar>
    </form>
  );
}

/** HU-014: registrar una tarjeta. El número completo no se guarda. */
export function FormularioTarjeta() {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(guardarTarjeta, {});
  const v = estado.ok ? {} : (estado.valores ?? {});
  const c = estado.campos ?? {};
  return (
    <form action={accion} className="flex flex-col gap-4" noValidate key={JSON.stringify(estado)}>
      <Mensaje estado={estado} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Seleccion etiqueta="Tipo" nombre="tipo" defaultValue={v.tipo ?? "CREDITO"} error={c.tipo}>
          <option value="CREDITO">Crédito</option>
          <option value="DEBITO">Débito</option>
        </Seleccion>
        <Seleccion etiqueta="Franquicia" nombre="franquicia" defaultValue={v.franquicia ?? "VISA"} error={c.franquicia}>
          <option value="VISA">Visa</option>
          <option value="MASTERCARD">Mastercard</option>
          <option value="AMERICAN EXPRESS">American Express</option>
          <option value="DINERS">Diners</option>
        </Seleccion>
      </div>
      <Campo etiqueta="Titular" nombre="titular" defaultValue={v.titular} error={c.titular} autoComplete="cc-name" required />
      <div className="grid gap-4 sm:grid-cols-[1fr_140px]">
        <Campo etiqueta="Número de la tarjeta" nombre="numero" inputMode="numeric" autoComplete="off" error={c.numero} required />
        <Campo etiqueta="Vence (MM/AA)" nombre="vencimiento" placeholder="08/29" defaultValue={v.vencimiento} error={c.vencimiento} required />
      </div>
      <p className="text-xs text-tinta-suave">Solo guardamos los últimos cuatro dígitos.</p>
      <BotonEnviar className="self-end">Agregar tarjeta</BotonEnviar>
    </form>
  );
}

/** HU-014 · RF-70: el cliente edita su saldo; queda como movimiento. */
export function FormularioSaldo({ saldo }: { saldo: string }) {
  const [estado, accion] = useActionState<EstadoFormulario, FormData>(ajustarSaldo, {});
  const valor = estado.valores?.saldo ?? saldo;
  return (
    <form action={accion} className="flex flex-col gap-3" noValidate key={JSON.stringify(estado)}>
      <Mensaje estado={estado} />
      <Campo
        etiqueta="Nuevo saldo"
        nombre="saldo"
        inputMode="numeric"
        defaultValue={String(Math.round(Number(valor)))}
        error={estado.campos?.saldo}
        ayuda="En pesos, sin puntos."
      />
      <BotonEnviar className="self-end">Actualizar saldo</BotonEnviar>
    </form>
  );
}
