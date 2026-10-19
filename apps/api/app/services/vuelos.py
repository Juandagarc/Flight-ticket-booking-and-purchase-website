"""Reglas del módulo de administración de vuelos (CU-06, CU-07, CU-08, CU-16, CU-17)."""

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errores import ErrorNegocio
from app.models import Ciudad, Vuelo

NACIONAL = "NACIONAL"
INTERNACIONAL = "INTERNACIONAL"
RADIO_TIERRA_KM = 6371.0088


def distancia_km(a: Ciudad, b: Ciudad) -> float:
    """Distancia ortodrómica (fórmula del haversine) entre dos ciudades del catálogo."""
    lat1, lon1, lat2, lon2 = map(
        math.radians, (float(a.latitud), float(a.longitud), float(b.latitud), float(b.longitud))
    )
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(h))


def duracion_minutos(a: Ciudad, b: Ciudad) -> int:
    """RF-53: tiempo de vuelo = distancia / velocidad promedio, redondeado al minuto superior."""
    velocidad = get_settings().velocidad_promedio_kmh
    return max(1, math.ceil(distancia_km(a, b) / velocidad * 60))


def salida_utc(origen: Ciudad, fecha: date, hora: time) -> datetime:
    """La fecha y hora que digita el administrador son las locales de la ciudad de origen."""
    local = datetime.combine(fecha, hora).replace(tzinfo=ZoneInfo(origen.zona_horaria))
    return local.astimezone(UTC)


def llegada_local(salida: datetime, minutos: int, destino: Ciudad) -> datetime:
    """RF-02: fecha y hora de llegada en la hora local del destino (sin zona, como en la tabla)."""
    llegada = salida.astimezone(UTC) + timedelta(minutes=minutos)
    return llegada.astimezone(ZoneInfo(destino.zona_horaria)).replace(tzinfo=None)


def salida_local(vuelo: Vuelo) -> datetime:
    return vuelo.fecha_hora_salida.astimezone(ZoneInfo(vuelo.ciudad_origen.zona_horaria)).replace(tzinfo=None)


def obtener_ciudad(db: Session, codigo: str, campo: str) -> Ciudad:
    ciudad = db.get(Ciudad, codigo.upper())
    if ciudad is None:
        raise ErrorNegocio(
            422, "CIUDAD_FUERA_DE_CATALOGO", "La ciudad no está en el catálogo permitido.", campo
        )
    return ciudad


def tipo_de_ruta(origen: Ciudad, destino: Ciudad) -> str:
    """RF-03 a RF-05 y RF-49: decide el tipo de vuelo o rechaza la ruta."""
    if origen.codigo == destino.codigo:
        raise ErrorNegocio(
            422, "ORIGEN_IGUAL_DESTINO", "El origen y el destino deben ser distintos.", "destino"
        )
    if origen.es_capital_nacional and destino.es_capital_nacional:
        return NACIONAL
    if origen.origen_internacional and destino.destino_internacional:
        return INTERNACIONAL
    raise ErrorNegocio(
        422,
        "RUTA_NO_PERMITIDA",
        "Ruta no permitida: los nacionales van entre capitales departamentales y los "
        "internacionales salen de Pereira, Bogotá, Medellín, Cali o Cartagena hacia Madrid, "
        "Londres, New York, Buenos Aires o Miami.",
        "destino",
    )


def siguiente_codigo(db: Session) -> str:
    """RF-54: dos letras de la aerolínea seguidas de un consecutivo (FL0001, FL0002…)."""
    n = db.execute(text("SELECT nextval('vuelo_consecutivo')")).scalar_one()
    return f"{get_settings().aerolinea_codigo}{n:04d}"


def tiquetes_vigentes(db: Session, codigos: list[str]) -> dict[str, dict[str, int]]:
    """Tiquetes no cancelados por vuelo y clase de reservas vigentes o pagadas.

    Una reserva bloquea sillas igual que una compra (RF-55), así que ambas cuentan.
    """
    if not codigos:
        return {}
    filas = db.execute(
        text(
            """
            SELECT t.vuelo_codigo, t.clase, count(*)
            FROM tiquete t JOIN reserva r ON r.codigo = t.reserva_codigo
            WHERE t.vuelo_codigo = ANY(:codigos)
              AND t.estado <> 'CANCELADO'
              AND r.estado IN ('RESERVADA', 'PAGADA')
            GROUP BY t.vuelo_codigo, t.clase
            """
        ),
        {"codigos": codigos},
    ).all()
    resultado: dict[str, dict[str, int]] = {}
    for codigo, clase, n in filas:
        resultado.setdefault(codigo, {})[clase] = n
    return resultado


def disponibles(vuelo: Vuelo, ocupados: dict[str, int]) -> dict[str, int]:
    cfg = vuelo.configuracion
    primera = cfg.ultima_silla_primera
    economica = cfg.capacidad - cfg.ultima_silla_primera
    return {
        "primera": primera - ocupados.get("PRIMERA", 0),
        "economica": economica - ocupados.get("ECONOMICA", 0),
    }


def es_editable(vuelo: Vuelo, ocupados: dict[str, int], ahora: datetime | None = None) -> bool:
    """RF-08 (Vuelo.esEditable): programado, que no ha sucedido y sin tiquetes vendidos."""
    ahora = ahora or datetime.now(UTC)
    return vuelo.estado == "PROGRAMADO" and vuelo.fecha_hora_salida > ahora and sum(ocupados.values()) == 0


def precio_noticia(primera: Decimal, economica: Decimal) -> Decimal:
    """Precio unitario de la noticia: la tarifa más baja del vuelo («desde»)."""
    return min(primera, economica)


def imagen_por_defecto(destino: Ciudad) -> str:
    """Imagen alusiva al destino que sirve la aplicación web (RF-10, RF-65)."""
    return f"/destinos/{destino.codigo}.svg"


@dataclass
class Ruta:
    origen: Ciudad
    destino: Ciudad
    tipo: str
    salida: datetime
    duracion: int
    llegada: datetime


def calcular_ruta(db: Session, origen: str, destino: str, fecha: date, hora: time) -> Ruta:
    c_origen = obtener_ciudad(db, origen, "origen")
    c_destino = obtener_ciudad(db, destino, "destino")
    tipo = tipo_de_ruta(c_origen, c_destino)
    salida = salida_utc(c_origen, fecha, hora)
    if salida <= datetime.now(UTC):
        raise ErrorNegocio(
            422, "SALIDA_EN_EL_PASADO", "La fecha y hora de salida deben ser futuras.", "fecha_salida"
        )
    minutos = duracion_minutos(c_origen, c_destino)
    return Ruta(c_origen, c_destino, tipo, salida, minutos, llegada_local(salida, minutos, c_destino))


def contar_vuelos(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Vuelo)) or 0
