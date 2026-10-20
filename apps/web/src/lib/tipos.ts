export type Rol = "ROOT" | "ADMINISTRADOR" | "CLIENTE";

export interface Perfil {
  documento: string;
  tipo_documento: "CEDULA" | "PASAPORTE";
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string;
  lugar_nacimiento: string;
  direccion_facturacion: string;
  genero: "FEMENINO" | "MASCULINO" | "OTRO";
  correo: string;
  imagen_url: string | null;
}

export interface UsuarioDetalle {
  id: string;
  nombre_usuario: string;
  rol: Rol;
  perfil: Perfil | null;
  perfil_completo: boolean;
}

export interface Administrador {
  id: string;
  nombre_usuario: string;
  rol: Rol;
  fecha_creacion: string;
  activo: boolean;
}

export interface Ciudad {
  codigo: string;
  nombre: string;
  pais: string;
  zona_horaria: string;
  es_capital_nacional: boolean;
  origen_internacional: boolean;
  destino_internacional: boolean;
}

export interface CiudadCorta {
  codigo: string;
  nombre: string;
  pais: string;
}

export interface Vuelo {
  codigo: string;
  tipo: "NACIONAL" | "INTERNACIONAL";
  origen: CiudadCorta;
  destino: CiudadCorta;
  salida_local: string;
  salida_utc: string;
  duracion_min: number;
  llegada_local: string;
  estado: "PROGRAMADO" | "CANCELADO" | "REALIZADO";
  imagen_url: string;
  tarifas: { primera: string; economica: string };
  disponibles: { primera: number; economica: number };
  editable: boolean;
}

export interface ResultadoBusqueda {
  total: number;
  vuelos: Vuelo[];
}

export interface Noticia {
  id: string;
  tipo: "NUEVO_VUELO" | "PROMOCION";
  titulo: string;
  imagen_url: string;
  precio_unitario: string;
  fecha_publicacion: string;
  vuelo_codigo: string;
  origen: CiudadCorta;
  destino: CiudadCorta;
  salida_local: string;
  llegada_local: string;
}

export interface Actividad {
  tipo: string;
  fecha: string;
  origen: string | null;
  destino: string | null;
  fecha_desde: string | null;
  fecha_hasta: string | null;
  precio_min: string | null;
  precio_max: string | null;
  pasajeros: number | null;
}

/** Estado que devuelven las acciones de los formularios. */
export interface EstadoFormulario {
  ok?: boolean;
  mensaje?: string;
  campos?: Record<string, string>;
  valores?: Record<string, string>;
}
