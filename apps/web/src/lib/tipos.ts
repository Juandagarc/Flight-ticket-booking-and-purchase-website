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

export type Clase = "PRIMERA" | "ECONOMICA";
export type EstadoReserva = "RESERVADA" | "PAGADA" | "CANCELADA" | "VENCIDA";

export interface Tramo {
  vuelo_codigo: string;
  tipo_vuelo: "NACIONAL" | "INTERNACIONAL";
  origen: CiudadCorta;
  destino: CiudadCorta;
  salida_local: string;
  llegada_local: string;
  duracion_min: number;
  clase: Clase;
  viajeros: number;
  precio_unitario: string;
  subtotal: string;
}

export interface ReservaResumen {
  codigo: string;
  estado: EstadoReserva;
  tipo_trayecto: "SENCILLO" | "IDA_Y_VUELTA";
  clase: Clase;
  tramos: Tramo[];
  viajeros: number;
  total: string;
  fecha_creacion: string;
  fecha_expiracion: string | null;
  en_carrito: boolean;
  puede_pagar: boolean;
  puede_cancelar: boolean;
  limite_cancelacion: string | null;
}

export interface Tiquete {
  id: string;
  vuelo_codigo: string;
  origen: CiudadCorta;
  destino: CiudadCorta;
  tipo_vuelo: string;
  salida_local: string;
  llegada_local: string;
  pasajero_documento: string;
  pasajero_nombre: string;
  silla: number;
  fila: number;
  columna: string;
  posicion: "VENTANA" | "CENTRO" | "PASILLO";
  clase: Clase;
  precio: string;
  estado: string;
  checkin: "PENDIENTE" | "REALIZADO";
}

export interface ReservaDetalle extends ReservaResumen {
  tiquetes: Tiquete[];
  pago_fecha: string | null;
  reembolso: string | null;
  reembolso_fecha: string | null;
}

export interface Carrito {
  reservas: ReservaResumen[];
  total: string;
  saldo: string;
}

export interface Pago {
  id: string;
  monto_total: string;
  fecha: string;
  reservas: string[];
  saldo: string;
}

export interface TarjetaGuardada {
  id: string;
  tipo: "CREDITO" | "DEBITO";
  franquicia: string;
  titular: string;
  ultimos_digitos: string;
  vencimiento: string;
}

export interface Movimiento {
  id: string;
  tipo: "AJUSTE_MANUAL" | "DEBITO_COMPRA" | "ABONO_REEMBOLSO";
  monto: string;
  fecha: string;
  saldo_resultante: string;
  descripcion: string | null;
}

export interface Monedero {
  saldo: string;
  tarjetas: TarjetaGuardada[];
  movimientos: Movimiento[];
}
