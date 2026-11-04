"""Esquemas de entrada y salida de la API."""

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TipoDocumento = Literal["CEDULA", "PASAPORTE"]
Genero = Literal["FEMENINO", "MASCULINO", "OTRO"]

Documento = Annotated[str, Field(pattern=r"^[A-Za-z0-9]{4,20}$")]
NombreUsuario = Annotated[str, Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")]
# RF-62: el cambio de contraseña no tiene restricciones adicionales; solo se exige que no esté vacía.
Contrasena = Annotated[str, Field(min_length=1, max_length=128)]


def _texto(maximo: int):
    return Annotated[str, Field(min_length=1, max_length=maximo)]


class _Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --- Usuarios ---------------------------------------------------------------------


class DatosPerfilEditables(_Entrada):
    nombres: _texto(80)
    apellidos: _texto(80)
    fecha_nacimiento: date
    lugar_nacimiento: _texto(100)
    direccion_facturacion: _texto(200)
    genero: Genero
    correo: EmailStr
    imagen_url: Annotated[str, Field(max_length=300)] | None = None

    @field_validator("fecha_nacimiento")
    @classmethod
    def _no_futura(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy.")
        return v

    @field_validator("imagen_url")
    @classmethod
    def _vacia_es_nula(cls, v: str | None) -> str | None:
        return v or None


class PerfilNuevo(DatosPerfilEditables):
    documento: Documento
    tipo_documento: TipoDocumento


class RegistroCliente(PerfilNuevo):
    nombre_usuario: NombreUsuario
    contrasena: Contrasena


class PerfilSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    documento: str
    tipo_documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    lugar_nacimiento: str
    direccion_facturacion: str
    genero: str
    correo: str
    imagen_url: str | None


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre_usuario: str
    rol: str


class UsuarioDetalle(UsuarioSalida):
    perfil: PerfilSalida | None = None
    perfil_completo: bool = False


class Credenciales(_Entrada):
    nombre_usuario: Annotated[str, Field(min_length=1, max_length=50)]
    contrasena: Annotated[str, Field(min_length=1, max_length=128)]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSalida


class CambioContrasena(_Entrada):
    actual: Contrasena
    nueva: Contrasena
    confirmacion: Contrasena


class AdministradorNuevo(_Entrada):
    nombre_usuario: NombreUsuario
    contrasena: Contrasena


class AdministradorSalida(UsuarioSalida):
    fecha_creacion: datetime
    activo: bool


# --- Vuelos -----------------------------------------------------------------------


class CiudadSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    pais: str
    zona_horaria: str
    es_capital_nacional: bool
    origen_internacional: bool
    destino_internacional: bool


class CiudadCorta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    pais: str


Dinero = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]


class VueloNuevo(_Entrada):
    origen: Annotated[str, Field(min_length=3, max_length=5)]
    destino: Annotated[str, Field(min_length=3, max_length=5)]
    fecha_salida: date
    hora_salida: time
    tarifa_primera: Dinero
    tarifa_economica: Dinero
    imagen_url: Annotated[str, Field(max_length=300)] | None = None


class VueloEdicion(_Entrada):
    """Edición parcial (RF-08): fecha, hora, ruta o tarifas. El código no se edita."""

    origen: Annotated[str, Field(min_length=3, max_length=5)] | None = None
    destino: Annotated[str, Field(min_length=3, max_length=5)] | None = None
    fecha_salida: date | None = None
    hora_salida: time | None = None
    tarifa_primera: Dinero | None = None
    tarifa_economica: Dinero | None = None
    imagen_url: Annotated[str, Field(max_length=300)] | None = None


class TarifasSalida(BaseModel):
    primera: Decimal
    economica: Decimal


class DisponibilidadSalida(BaseModel):
    primera: int
    economica: int


class VueloSalida(BaseModel):
    codigo: str
    tipo: str
    origen: CiudadCorta
    destino: CiudadCorta
    salida_local: datetime = Field(description="Fecha y hora de salida en la hora local del origen")
    salida_utc: datetime
    duracion_min: int
    llegada_local: datetime = Field(description="Fecha y hora de llegada en la hora local del destino")
    estado: str
    imagen_url: str
    tarifas: TarifasSalida
    disponibles: DisponibilidadSalida
    editable: bool


class ResultadoBusqueda(BaseModel):
    total: int
    vuelos: list[VueloSalida]


# --- Noticias ---------------------------------------------------------------------


class NoticiaSalida(BaseModel):
    id: uuid.UUID
    tipo: str
    titulo: str
    imagen_url: str
    precio_unitario: Decimal
    fecha_publicacion: datetime
    vuelo_codigo: str
    origen: CiudadCorta
    destino: CiudadCorta
    salida_local: datetime
    llegada_local: datetime


class ActividadSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: str
    fecha: datetime
    origen: str | None
    destino: str | None
    fecha_desde: date | None
    fecha_hasta: date | None
    precio_min: Decimal | None
    precio_max: Decimal | None
    pasajeros: int | None


# --- Iteración 2: reserva, compra y monedero ---------------------------------------

Clase = Literal["PRIMERA", "ECONOMICA"]
Telefono = Annotated[str, Field(pattern=r"^\+?[0-9][0-9 ]{6,18}$")]


class PasajeroEntrada(_Entrada):
    """RF-16: datos de cada viajero."""

    documento: Documento
    nombres: _texto(80)
    apellidos: _texto(80)
    fecha_nacimiento: date
    genero: Genero
    telefono: Telefono
    correo: EmailStr
    nombre_contacto: _texto(120)
    telefono_contacto: Telefono

    @field_validator("fecha_nacimiento")
    @classmethod
    def _no_futura(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy.")
        return v


class ReservaNueva(_Entrada):
    vuelo_codigo: Annotated[str, Field(min_length=3, max_length=10)]
    vuelo_regreso_codigo: Annotated[str, Field(min_length=3, max_length=10)] | None = None
    clase: Clase
    pasajeros: Annotated[list[PasajeroEntrada], Field(min_length=1, max_length=5)]


class PagoNuevo(_Entrada):
    reservas: Annotated[
        list[Annotated[str, Field(min_length=6, max_length=6)]], Field(min_length=1, max_length=20)
    ]


class TiqueteSalida(BaseModel):
    id: uuid.UUID
    vuelo_codigo: str
    origen: CiudadCorta
    destino: CiudadCorta
    tipo_vuelo: str
    salida_local: datetime
    llegada_local: datetime
    pasajero_documento: str
    pasajero_nombre: str
    silla: int
    fila: int
    columna: str
    posicion: str
    clase: str
    precio: Decimal
    estado: str
    checkin: str


class TramoSalida(BaseModel):
    vuelo_codigo: str
    tipo_vuelo: str
    origen: CiudadCorta
    destino: CiudadCorta
    salida_local: datetime
    llegada_local: datetime
    duracion_min: int
    clase: str
    viajeros: int
    precio_unitario: Decimal
    subtotal: Decimal


class ReservaResumen(BaseModel):
    codigo: str
    estado: str
    tipo_trayecto: str
    clase: str
    tramos: list[TramoSalida]
    viajeros: int
    total: Decimal
    fecha_creacion: datetime
    fecha_expiracion: datetime | None
    en_carrito: bool
    puede_pagar: bool
    puede_cancelar: bool
    limite_cancelacion: datetime | None


class ReservaDetalle(ReservaResumen):
    tiquetes: list[TiqueteSalida]
    pago_fecha: datetime | None = None
    reembolso: Decimal | None = None
    reembolso_fecha: datetime | None = None


class CarritoSalida(BaseModel):
    reservas: list[ReservaResumen]
    total: Decimal
    saldo: Decimal


class PagoSalida(BaseModel):
    id: uuid.UUID
    monto_total: Decimal
    fecha: datetime
    reservas: list[str]
    saldo: Decimal


class TarjetaNueva(_Entrada):
    tipo: Literal["CREDITO", "DEBITO"]
    franquicia: Literal["VISA", "MASTERCARD", "AMERICAN EXPRESS", "DINERS"]
    titular: _texto(120)
    numero: Annotated[str, Field(min_length=13, max_length=23)]
    vencimiento: Annotated[str, Field(pattern=r"^(0[1-9]|1[0-2])/[0-9]{2}$")]

    @field_validator("numero")
    @classmethod
    def _luhn(cls, v: str) -> str:
        digitos = v.replace(" ", "").replace("-", "")
        if not digitos.isdigit() or not 13 <= len(digitos) <= 19:
            raise ValueError("El número de la tarjeta debe tener entre 13 y 19 dígitos.")
        suma = 0
        for i, d in enumerate(reversed(digitos)):
            n = int(d)
            if i % 2 == 1:
                n = n * 2 - 9 if n > 4 else n * 2
            suma += n
        if suma % 10:
            raise ValueError("El número de la tarjeta no es válido.")
        return digitos

    @field_validator("vencimiento")
    @classmethod
    def _vigente(cls, v: str) -> str:
        mes, anio = int(v[:2]), 2000 + int(v[3:])
        hoy = date.today()
        if (anio, mes) < (hoy.year, hoy.month):
            raise ValueError("La tarjeta está vencida.")
        return v


class TarjetaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: str
    franquicia: str
    titular: str
    ultimos_digitos: str
    vencimiento: str


class MovimientoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: str
    monto: Decimal
    fecha: datetime
    saldo_resultante: Decimal
    descripcion: str | None


class MonederoSalida(BaseModel):
    saldo: Decimal
    tarjetas: list[TarjetaSalida]
    movimientos: list[MovimientoSalida]


class AjusteSaldo(_Entrada):
    saldo: Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
