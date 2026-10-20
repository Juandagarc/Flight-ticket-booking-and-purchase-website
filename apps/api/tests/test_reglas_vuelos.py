"""Pruebas unitarias de las reglas de cálculo de vuelos (sin base de datos)."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.errores import ErrorNegocio
from app.services import vuelos as reglas


def ciudad(codigo, lat, lon, zona="America/Bogota", nacional=True, oi=False, di=False):
    return SimpleNamespace(
        codigo=codigo,
        latitud=Decimal(str(lat)),
        longitud=Decimal(str(lon)),
        zona_horaria=zona,
        es_capital_nacional=nacional,
        origen_internacional=oi,
        destino_internacional=di,
    )


BOG = ciudad("BOG", 4.7110, -74.0721, oi=True)
MDE = ciudad("MDE", 6.2442, -75.5812, oi=True)
BGA = ciudad("BGA", 7.1193, -73.1227)
MAD = ciudad("MAD", 40.4168, -3.7038, "Europe/Madrid", nacional=False, di=True)
LON = ciudad("LON", 51.5074, -0.1278, "Europe/London", nacional=False, di=True)


def test_distancia_haversine_conocida():
    assert 230 <= reglas.distancia_km(BOG, MDE) <= 245  # centros de ciudad
    assert 8000 <= reglas.distancia_km(BOG, MAD) <= 8100


def test_duracion_es_distancia_entre_velocidad():
    km = reglas.distancia_km(BOG, MAD)
    assert reglas.duracion_minutos(BOG, MAD) == pytest.approx(km / 800 * 60, abs=1)


def test_tipo_de_ruta():
    assert reglas.tipo_de_ruta(BOG, MDE) == "NACIONAL"
    assert reglas.tipo_de_ruta(BOG, MAD) == "INTERNACIONAL"
    with pytest.raises(ErrorNegocio) as e:
        reglas.tipo_de_ruta(BGA, MAD)
    assert e.value.codigo == "RUTA_NO_PERMITIDA"
    with pytest.raises(ErrorNegocio):
        reglas.tipo_de_ruta(MAD, LON)
    with pytest.raises(ErrorNegocio) as e:
        reglas.tipo_de_ruta(BOG, BOG)
    assert e.value.codigo == "ORIGEN_IGUAL_DESTINO"


def test_hora_local_de_llegada_cruza_dia_y_horario_de_verano():
    # 20:00 en Bogotá un 10 de julio = 01:00 UTC del 11; Madrid está en UTC+2 en verano.
    salida = reglas.salida_utc(BOG, date(2027, 7, 10), time(20, 0))
    assert salida == datetime(2027, 7, 11, 1, 0, tzinfo=UTC)
    llegada = reglas.llegada_local(salida, 600, MAD)
    assert llegada == datetime(2027, 7, 11, 13, 0)
    # En enero Madrid está en UTC+1.
    salida = reglas.salida_utc(BOG, date(2027, 1, 10), time(20, 0))
    assert reglas.llegada_local(salida, 600, MAD) == datetime(2027, 1, 11, 12, 0)


def test_es_editable():
    vuelo = SimpleNamespace(estado="PROGRAMADO", fecha_hora_salida=datetime.now(UTC) + timedelta(days=1))
    assert reglas.es_editable(vuelo, {}) is True
    assert reglas.es_editable(vuelo, {"ECONOMICA": 1}) is False
    vuelo.fecha_hora_salida = datetime.now(UTC) - timedelta(minutes=1)
    assert reglas.es_editable(vuelo, {}) is False
    vuelo.fecha_hora_salida = datetime.now(UTC) + timedelta(days=1)
    vuelo.estado = "REALIZADO"
    assert reglas.es_editable(vuelo, {}) is False


def test_precio_noticia_es_la_tarifa_mas_baja():
    assert reglas.precio_noticia(Decimal("500"), Decimal("200")) == Decimal("200")
