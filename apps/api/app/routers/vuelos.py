"""HU-006 Programación (CU-06), HU-007 Edición (CU-08) y HU-008 Búsqueda de vuelos (CU-20, CU-21)."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, aliased

from app.db import get_db
from app.deps import requiere_administrador, usuario_opcional
from app.errores import ErrorNegocio
from app.models import ActividadUsuario, Ciudad, Rol, Tarifa, Usuario, Vuelo
from app.schemas import (
    CiudadCorta,
    CiudadSalida,
    DisponibilidadSalida,
    ResultadoBusqueda,
    TarifasSalida,
    VueloEdicion,
    VueloNuevo,
    VueloSalida,
)
from app.services import notificaciones
from app.services import vuelos as reglas

router = APIRouter(tags=["Vuelos"])


def a_salida(vuelo: Vuelo, ocupados: dict[str, int]) -> VueloSalida:
    return VueloSalida(
        codigo=vuelo.codigo,
        tipo=vuelo.tipo,
        origen=CiudadCorta.model_validate(vuelo.ciudad_origen),
        destino=CiudadCorta.model_validate(vuelo.ciudad_destino),
        salida_local=reglas.salida_local(vuelo),
        salida_utc=vuelo.fecha_hora_salida.astimezone(UTC),
        duracion_min=vuelo.duracion_min,
        llegada_local=vuelo.llegada_local,
        estado=vuelo.estado,
        imagen_url=vuelo.imagen_url,
        tarifas=TarifasSalida(primera=vuelo.tarifa("PRIMERA"), economica=vuelo.tarifa("ECONOMICA")),
        disponibles=DisponibilidadSalida(**reglas.disponibles(vuelo, ocupados)),
        editable=reglas.es_editable(vuelo, ocupados),
    )


def _salidas(db: Session, vuelos: list[Vuelo]) -> list[VueloSalida]:
    ocupacion = reglas.tiquetes_vigentes(db, [v.codigo for v in vuelos])
    return [a_salida(v, ocupacion.get(v.codigo, {})) for v in vuelos]


def _vuelo_o_404(db: Session, codigo: str) -> Vuelo:
    vuelo = db.get(Vuelo, codigo.upper())
    if vuelo is None:
        raise ErrorNegocio(404, "VUELO_NO_ENCONTRADO", "El vuelo no existe.")
    return vuelo


# --- Catálogo -------------------------------------------------------------------


@router.get("/ciudades", response_model=list[CiudadSalida], tags=["Catálogo"])
def listar_ciudades(db: Session = Depends(get_db)):
    """Catálogo de ciudades (CU-07): 32 capitales y las ciudades internacionales permitidas."""
    return db.scalars(select(Ciudad).order_by(Ciudad.nombre)).all()


# --- Administración --------------------------------------------------------------


@router.post("/vuelos", response_model=VueloSalida, status_code=status.HTTP_201_CREATED)
def programar_vuelo(
    datos: VueloNuevo,
    admin: Usuario = Depends(requiere_administrador),
    db: Session = Depends(get_db),
):
    """Programa un vuelo directo. El código, el tiempo y la llegada los calcula el sistema.

    Al guardarse, el vuelo se publica en Noticias (CU-16) y se avisa a los suscriptores (CU-17).
    """
    ruta = reglas.calcular_ruta(db, datos.origen, datos.destino, datos.fecha_salida, datos.hora_salida)
    vuelo = Vuelo(
        codigo=reglas.siguiente_codigo(db),
        tipo=ruta.tipo,
        origen=ruta.origen.codigo,
        destino=ruta.destino.codigo,
        fecha_hora_salida=ruta.salida,
        duracion_min=ruta.duracion,
        llegada_local=ruta.llegada,
        estado="PROGRAMADO",
        imagen_url=datos.imagen_url or reglas.imagen_por_defecto(ruta.destino),
        administrador_id=admin.id,
        tarifas=[
            Tarifa(clase="PRIMERA", valor=datos.tarifa_primera),
            Tarifa(clase="ECONOMICA", valor=datos.tarifa_economica),
        ],
    )
    db.add(vuelo)
    db.flush()
    db.refresh(vuelo)
    noticia = notificaciones.publicar_vuelo(db, vuelo)
    notificaciones.avisar_suscriptores(db, vuelo, noticia)
    db.commit()
    return a_salida(vuelo, {})


@router.get("/vuelos/gestion", response_model=list[VueloSalida])
def listar_para_gestion(
    estado: str | None = None,
    _: Usuario = Depends(requiere_administrador),
    db: Session = Depends(get_db),
):
    """Hub de gestión de vuelos (pantalla 26): todos los vuelos con su estado y si se editan."""
    consulta = select(Vuelo).order_by(Vuelo.fecha_hora_salida)
    if estado:
        consulta = consulta.where(Vuelo.estado == estado.upper())
    return _salidas(db, list(db.scalars(consulta).unique()))


@router.put("/vuelos/{codigo}", response_model=VueloSalida)
def editar_vuelo(
    codigo: str,
    datos: VueloEdicion,
    _: Usuario = Depends(requiere_administrador),
    db: Session = Depends(get_db),
):
    """Edita fecha, hora, ruta o tarifas de un vuelo que no ha sucedido y sin tiquetes (RF-08)."""
    vuelo = _vuelo_o_404(db, codigo)
    ocupados = reglas.tiquetes_vigentes(db, [vuelo.codigo]).get(vuelo.codigo, {})
    if not reglas.es_editable(vuelo, ocupados):
        raise ErrorNegocio(
            409,
            "VUELO_NO_EDITABLE",
            "Este vuelo ya no se puede editar: ya ocurrió, no está programado o tiene tiquetes vendidos.",
        )

    cambios = datos.model_dump(exclude_unset=True)
    actual_local = reglas.salida_local(vuelo)
    origen = cambios.get("origen") or vuelo.origen
    destino = cambios.get("destino") or vuelo.destino
    fecha = cambios.get("fecha_salida") or actual_local.date()
    hora = cambios.get("hora_salida") or actual_local.time()

    if {"origen", "destino", "fecha_salida", "hora_salida"} & cambios.keys():
        ruta = reglas.calcular_ruta(db, origen, destino, fecha, hora)
        imagen_era_por_defecto = vuelo.imagen_url == reglas.imagen_por_defecto(vuelo.ciudad_destino)
        vuelo.tipo = ruta.tipo
        vuelo.origen = ruta.origen.codigo
        vuelo.destino = ruta.destino.codigo
        vuelo.fecha_hora_salida = ruta.salida
        vuelo.duracion_min = ruta.duracion
        vuelo.llegada_local = ruta.llegada
        if imagen_era_por_defecto and "imagen_url" not in cambios:
            vuelo.imagen_url = reglas.imagen_por_defecto(ruta.destino)
    if cambios.get("imagen_url"):
        vuelo.imagen_url = cambios["imagen_url"]
    for clase, campo in (("PRIMERA", "tarifa_primera"), ("ECONOMICA", "tarifa_economica")):
        if campo in cambios and cambios[campo] is not None:
            next(t for t in vuelo.tarifas if t.clase == clase).valor = cambios[campo]

    db.flush()
    db.expire(vuelo, ["ciudad_origen", "ciudad_destino", "configuracion"])
    notificaciones.actualizar_noticias_del_vuelo(db, vuelo)
    db.commit()
    db.refresh(vuelo)
    return a_salida(vuelo, {})


# --- Búsqueda pública ------------------------------------------------------------


@router.get("/vuelos/buscar", response_model=ResultadoBusqueda)
def buscar_vuelos(
    origen: str | None = None,
    destino: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    precio_min: Annotated[Decimal | None, Query(ge=0)] = None,
    precio_max: Annotated[Decimal | None, Query(ge=0)] = None,
    pasajeros: Annotated[int | None, Query(ge=1, le=5)] = None,
    usuario: Usuario | None = Depends(usuario_opcional),
    db: Session = Depends(get_db),
):
    """Búsqueda por origen, destino, rango de fechas, rango de precios y pasajeros (RF-68).

    Cada filtro funciona solo o combinado. Las fechas se comparan con la fecha local de salida
    en la ciudad de origen. Un vuelo cumple el rango de precios si alguna de sus tarifas cae en él.
    Solo se listan vuelos programados que aún no salen, ordenados por fecha de salida (RF-69).
    """
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise ErrorNegocio(
            422, "RANGO_FECHAS_INVALIDO", "La fecha inicial no puede ser posterior a la final.", "fecha_hasta"
        )
    if precio_min is not None and precio_max is not None and precio_min > precio_max:
        raise ErrorNegocio(
            422, "RANGO_PRECIOS_INVALIDO", "El precio mínimo no puede superar al máximo.", "precio_max"
        )

    c_origen = aliased(Ciudad)
    consulta = (
        select(Vuelo)
        .join(c_origen, c_origen.codigo == Vuelo.origen)
        .where(Vuelo.estado == "PROGRAMADO", Vuelo.fecha_hora_salida > datetime.now(UTC))
        .order_by(Vuelo.fecha_hora_salida)
    )
    if origen:
        consulta = consulta.where(Vuelo.origen == origen.upper())
    if destino:
        consulta = consulta.where(Vuelo.destino == destino.upper())
    fecha_local = func.date(func.timezone(c_origen.zona_horaria, Vuelo.fecha_hora_salida))
    if fecha_desde:
        consulta = consulta.where(fecha_local >= fecha_desde)
    if fecha_hasta:
        consulta = consulta.where(fecha_local <= fecha_hasta)
    if precio_min is not None or precio_max is not None:
        cond = [Tarifa.vuelo_codigo == Vuelo.codigo]
        if precio_min is not None:
            cond.append(Tarifa.valor >= precio_min)
        if precio_max is not None:
            cond.append(Tarifa.valor <= precio_max)
        consulta = consulta.where(exists().where(*cond))

    vuelos = list(db.scalars(consulta).unique())
    resultados = _salidas(db, vuelos)
    if pasajeros:
        resultados = [r for r in resultados if r.disponibles.primera + r.disponibles.economica >= pasajeros]

    if usuario is not None and usuario.rol == Rol.CLIENTE:
        # CU-21: las búsquedas del cliente quedan registradas para el recomendador (RF-60).
        db.add(
            ActividadUsuario(
                cliente_id=usuario.id,
                tipo="BUSQUEDA",
                fecha=datetime.now(UTC),
                origen=origen.upper() if origen else None,
                destino=destino.upper() if destino else None,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                precio_min=precio_min,
                precio_max=precio_max,
                pasajeros=pasajeros,
            )
        )
        db.commit()

    return ResultadoBusqueda(total=len(resultados), vuelos=resultados)


@router.get("/vuelos/{codigo}", response_model=VueloSalida)
def ver_vuelo(codigo: str, db: Session = Depends(get_db)):
    vuelo = _vuelo_o_404(db, codigo)
    return _salidas(db, [vuelo])[0]
