"""Mapeo ORM de las tablas del modelo relacional que usa la iteración 1.

El esquema completo lo crea la migración 0001 con el script SQL del modelo E-R
(sql/0001_modelo_relacional.sql); aquí solo se mapean las tablas que la API toca.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Rol:
    ROOT = "ROOT"
    ADMINISTRADOR = "ADMINISTRADOR"
    CLIENTE = "CLIENTE"


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nombre_usuario: Mapped[str] = mapped_column(String(50), unique=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(13))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    perfil: Mapped["Perfil | None"] = relationship(back_populates="usuario", uselist=False)


class Perfil(Base):
    __tablename__ = "perfil"

    documento: Mapped[str] = mapped_column(String(20), primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), unique=True)
    tipo_documento: Mapped[str] = mapped_column(String(9))
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str] = mapped_column(String(80))
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    lugar_nacimiento: Mapped[str] = mapped_column(String(100))
    direccion_facturacion: Mapped[str] = mapped_column(String(200))
    genero: Mapped[str] = mapped_column(String(10))
    correo: Mapped[str] = mapped_column(String(120))
    imagen_url: Mapped[str | None] = mapped_column(String(300))

    usuario: Mapped[Usuario] = relationship(back_populates="perfil")


class Monedero(Base):
    __tablename__ = "monedero"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), unique=True)
    saldo: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=text("0"))


class Carrito(Base):
    __tablename__ = "carrito"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), unique=True)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Ciudad(Base):
    __tablename__ = "ciudad"

    codigo: Mapped[str] = mapped_column(String(5), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    pais: Mapped[str] = mapped_column(String(60))
    zona_horaria: Mapped[str] = mapped_column(String(40))
    latitud: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    es_capital_nacional: Mapped[bool] = mapped_column(Boolean)
    origen_internacional: Mapped[bool] = mapped_column(Boolean)
    destino_internacional: Mapped[bool] = mapped_column(Boolean)


class ConfiguracionCabina(Base):
    __tablename__ = "configuracion_cabina"

    tipo_vuelo: Mapped[str] = mapped_column(String(13), primary_key=True)
    capacidad: Mapped[int] = mapped_column(SmallInteger)
    ultima_silla_primera: Mapped[int] = mapped_column(SmallInteger)
    columnas: Mapped[str] = mapped_column(String(10))


class Vuelo(Base):
    __tablename__ = "vuelo"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(13), ForeignKey("configuracion_cabina.tipo_vuelo"))
    origen: Mapped[str] = mapped_column(String(5), ForeignKey("ciudad.codigo"))
    destino: Mapped[str] = mapped_column(String(5), ForeignKey("ciudad.codigo"))
    fecha_hora_salida: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duracion_min: Mapped[int] = mapped_column(Integer)
    llegada_local: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    estado: Mapped[str] = mapped_column(String(10), server_default=text("'PROGRAMADO'"))
    imagen_url: Mapped[str] = mapped_column(String(300))
    administrador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    ciudad_origen: Mapped[Ciudad] = relationship(foreign_keys=[origen], lazy="joined")
    ciudad_destino: Mapped[Ciudad] = relationship(foreign_keys=[destino], lazy="joined")
    configuracion: Mapped[ConfiguracionCabina] = relationship(lazy="joined")
    tarifas: Mapped[list["Tarifa"]] = relationship(
        back_populates="vuelo", lazy="selectin", cascade="all, delete-orphan"
    )

    def tarifa(self, clase: str) -> Decimal | None:
        for t in self.tarifas:
            if t.clase == clase:
                return t.valor
        return None


class Tarifa(Base):
    __tablename__ = "tarifa"

    vuelo_codigo: Mapped[str] = mapped_column(String(10), ForeignKey("vuelo.codigo"), primary_key=True)
    clase: Mapped[str] = mapped_column(String(9), primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    vuelo: Mapped[Vuelo] = relationship(back_populates="tarifas")


class Noticia(Base):
    __tablename__ = "noticia"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    vuelo_codigo: Mapped[str] = mapped_column(String(10), ForeignKey("vuelo.codigo"))
    promocion_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    tipo: Mapped[str] = mapped_column(String(11))
    titulo: Mapped[str] = mapped_column(String(150))
    imagen_url: Mapped[str] = mapped_column(String(300))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    fecha_publicacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    vigente: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))

    vuelo: Mapped[Vuelo] = relationship(lazy="joined")


class Suscripcion(Base):
    __tablename__ = "suscripcion"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"), unique=True)
    fecha_alta: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    activa: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))


class Notificacion(Base):
    __tablename__ = "notificacion"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    suscripcion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suscripcion.id"))
    noticia_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("noticia.id"))
    canal: Mapped[str] = mapped_column(String(10))
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enviada: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    leida: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))


class ActividadUsuario(Base):
    __tablename__ = "actividad_usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuario.id"))
    tipo: Mapped[str] = mapped_column(String(8))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    vuelo_codigo: Mapped[str | None] = mapped_column(String(10), ForeignKey("vuelo.codigo"))
    origen: Mapped[str | None] = mapped_column(String(5))
    destino: Mapped[str | None] = mapped_column(String(5))
    fecha_desde: Mapped[date | None] = mapped_column(Date)
    fecha_hasta: Mapped[date | None] = mapped_column(Date)
    precio_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    precio_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    pasajeros: Mapped[int | None] = mapped_column(SmallInteger)
    tipo_trayecto: Mapped[str | None] = mapped_column(String(12))
