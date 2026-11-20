/** Datos de cada viajero (RF-16). */
export const CAMPOS_VIAJERO = [
  "documento",
  "nombres",
  "apellidos",
  "fecha_nacimiento",
  "genero",
  "telefono",
  "correo",
  "nombre_contacto",
  "telefono_contacto",
] as const;

/** Los errores de la API llegan como «pasajeros.1.documento»; el formulario usa «p1_documento». */
export function camposDelFormulario(campos: Record<string, string>) {
  const salida: Record<string, string> = {};
  for (const [k, v] of Object.entries(campos)) {
    const m = k.match(/^pasajeros\.(\d+)\.(\w+)$/);
    salida[m ? `p${m[1]}_${m[2]}` : k] = v;
  }
  return salida;
}
