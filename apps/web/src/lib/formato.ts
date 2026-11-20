const pesos = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

export function precio(valor: string | number): string {
  return pesos.format(Number(valor)).replace(/ /g, " ");
}

/** Las fechas de la API llegan sin zona y ya en la hora local que corresponde. */
function partes(fechaLocal: string) {
  const [fecha, hora = "00:00"] = fechaLocal.split("T");
  const [anio, mes, dia] = fecha.split("-").map(Number);
  return { anio, mes, dia, hora: hora.slice(0, 5) };
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

export function fechaCorta(fechaLocal: string): string {
  const { anio, mes, dia } = partes(fechaLocal);
  return `${dia} ${MESES[mes - 1]} ${anio}`;
}

export function hora(fechaLocal: string): string {
  return partes(fechaLocal).hora;
}

export function fechaHora(fechaLocal: string): string {
  return `${fechaCorta(fechaLocal)} · ${hora(fechaLocal)}`;
}

export function duracion(minutos: number): string {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h === 0) return `${m} min`;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

/** Días de diferencia entre la fecha de salida y la de llegada (para mostrar «+1»). */
export function diasDeDiferencia(salidaLocal: string, llegadaLocal: string): number {
  const a = partes(salidaLocal);
  const b = partes(llegadaLocal);
  const da = Date.UTC(a.anio, a.mes - 1, a.dia);
  const db = Date.UTC(b.anio, b.mes - 1, b.dia);
  return Math.round((db - da) / 86_400_000);
}

const momentoColombia = new Intl.DateTimeFormat("es-CO", {
  timeZone: "America/Bogota",
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

/** Fechas con zona (creación, vencimiento, pagos) en hora de Colombia. */
export function momento(iso: string): string {
  const p = Object.fromEntries(momentoColombia.formatToParts(new Date(iso)).map((x) => [x.type, x.value]));
  return `${p.day} ${String(p.month).replace(".", "")} ${p.year} · ${p.hour}:${p.minute}`;
}

export const ESTADO_RESERVA: Record<string, string> = {
  RESERVADA: "Reservada",
  PAGADA: "Pagada",
  CANCELADA: "Cancelada",
  VENCIDA: "Vencida",
};

export const CLASE: Record<string, string> = { PRIMERA: "Primera", ECONOMICA: "Económica" };

export const POSICION: Record<string, string> = { VENTANA: "Ventana", CENTRO: "Centro", PASILLO: "Pasillo" };

export const MOVIMIENTO: Record<string, string> = {
  AJUSTE_MANUAL: "Ajuste manual",
  DEBITO_COMPRA: "Compra",
  ABONO_REEMBOLSO: "Reembolso",
};
