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
