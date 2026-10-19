"""HU-006 · Programación de vuelos (CU-06, incluye CU-07, CU-16 y CU-17)."""

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text

from tests.ayudas_vuelos import suscribir
from tests.conftest import datos_vuelo, manana


def test_codigo_con_dos_letras_y_consecutivo(programar):
    a = programar()
    b = programar(destino="MDE")
    assert re.fullmatch(r"FL\d{4}", a["codigo"])
    assert int(b["codigo"][2:]) == int(a["codigo"][2:]) + 1


def test_el_codigo_no_se_puede_digitar_ni_editar(client, admin_headers, programar):
    r = client.post("/vuelos", json={**datos_vuelo(), "codigo": "XX9999"}, headers=admin_headers)
    assert r.status_code == 422
    vuelo = programar()
    r = client.put(f"/vuelos/{vuelo['codigo']}", json={"codigo": "XX9999"}, headers=admin_headers)
    assert r.status_code == 422
    assert client.get(f"/vuelos/{vuelo['codigo']}").status_code == 200


def test_tiempo_y_llegada_se_calculan_no_se_digitan(client, admin_headers, programar):
    r = client.post("/vuelos", json={**datos_vuelo(), "duracion_min": 30}, headers=admin_headers)
    assert r.status_code == 422  # el administrador no envía el tiempo de vuelo

    fecha = manana(15)
    vuelo = programar(origen="PEI", destino="MAD", fecha_salida=fecha, hora_salida="20:00")
    assert vuelo["tipo"] == "INTERNACIONAL"
    # Distancia ortodrómica Pereira–Madrid ≈ 8 400 km a 800 km/h ≈ 10,5 h.
    assert 600 <= vuelo["duracion_min"] <= 680
    salida = datetime.fromisoformat(f"{fecha}T20:00").replace(tzinfo=ZoneInfo("America/Bogota"))
    esperada = (salida + timedelta(minutes=vuelo["duracion_min"])).astimezone(ZoneInfo("Europe/Madrid"))
    assert vuelo["llegada_local"] == esperada.replace(tzinfo=None).isoformat()
    assert vuelo["salida_local"] == f"{fecha}T20:00:00"


def test_vuelo_nacional_entre_capitales(programar):
    vuelo = programar(origen="LET", destino="ADZ")
    assert vuelo["tipo"] == "NACIONAL"
    assert vuelo["disponibles"] == {"primera": 25, "economica": 125}
    internacional = programar(origen="CTG", destino="MIA")
    assert internacional["disponibles"] == {"primera": 50, "economica": 200}


@pytest.mark.parametrize(
    ("origen", "destino", "codigo"),
    [
        ("PEI", "XYZ", "CIUDAD_FUERA_DE_CATALOGO"),
        ("ABC", "BOG", "CIUDAD_FUERA_DE_CATALOGO"),
        ("BOG", "BOG", "ORIGEN_IGUAL_DESTINO"),
        ("BGA", "MAD", "RUTA_NO_PERMITIDA"),  # Bucaramanga no es origen internacional
        ("MAD", "BOG", "RUTA_NO_PERMITIDA"),  # Madrid no es origen permitido (P-06 abierta)
        ("MAD", "LON", "RUTA_NO_PERMITIDA"),
    ],
)
def test_no_acepta_rutas_fuera_del_catalogo(client, admin_headers, origen, destino, codigo):
    r = client.post("/vuelos", json=datos_vuelo(origen=origen, destino=destino), headers=admin_headers)
    assert r.status_code == 422
    assert r.json()["detail"]["codigo"] == codigo


def test_no_acepta_salida_en_el_pasado(client, admin_headers):
    r = client.post("/vuelos", json=datos_vuelo(fecha_salida="2020-01-01"), headers=admin_headers)
    assert r.status_code == 422
    assert r.json()["detail"]["codigo"] == "SALIDA_EN_EL_PASADO"


def test_tarifas_obligatorias_y_positivas(client, admin_headers):
    datos = datos_vuelo(tarifa_economica="0")
    assert client.post("/vuelos", json=datos, headers=admin_headers).status_code == 422
    datos = datos_vuelo()
    del datos["tarifa_primera"]
    assert client.post("/vuelos", json=datos, headers=admin_headers).status_code == 422


def test_solo_el_administrador_programa(client, root_headers, cliente_headers):
    for headers in (root_headers, cliente_headers, {}):
        assert client.post("/vuelos", json=datos_vuelo(), headers=headers).status_code in (401, 403)


def test_al_guardar_aparece_en_noticias(client, programar):
    vuelo = programar(origen="BOG", destino="MAD")
    noticias = client.get("/noticias").json()
    assert len(noticias) == 1
    n = noticias[0]
    assert n["vuelo_codigo"] == vuelo["codigo"]
    assert n["tipo"] == "NUEVO_VUELO"
    assert n["origen"]["nombre"] == "Bogotá" and n["destino"]["nombre"] == "Madrid"
    assert float(n["precio_unitario"]) == 280000
    assert n["imagen_url"] == "/destinos/MAD.svg"


def test_al_guardar_los_suscriptores_reciben_el_aviso(client, db, buzon, registrar, programar):
    registrar()
    registrar(documento="55667788", nombre_usuario="pedro", correo="pedro@example.com")
    suscribir(db, "analopez")  # pedro no está suscrito

    vuelo = programar(origen="PEI", destino="CTG")

    assert [c.para for c in buzon.enviados] == ["ana@example.com"]
    assert vuelo["codigo"] in buzon.enviados[0].cuerpo
    canales = db.execute(text("SELECT canal, enviada FROM notificacion ORDER BY canal")).all()
    assert canales == [("APLICACION", True), ("CORREO", True)]


def test_un_fallo_de_correo_no_impide_programar(client, db, buzon, registrar, programar):
    registrar()
    suscribir(db)

    def falla(_):
        raise ConnectionError("SMTP caído")

    buzon.enviar = falla
    vuelo = programar()
    assert vuelo["codigo"]
    assert db.execute(text("SELECT enviada FROM notificacion WHERE canal = 'CORREO'")).scalar_one() is False


def test_catalogo_de_ciudades(client):
    ciudades = client.get("/ciudades").json()
    assert len(ciudades) == 37
    assert sum(c["es_capital_nacional"] for c in ciudades) == 32
    assert {c["nombre"] for c in ciudades if c["origen_internacional"]} == {
        "Pereira",
        "Bogotá",
        "Medellín",
        "Cali",
        "Cartagena",
    }
    assert {c["nombre"] for c in ciudades if c["destino_internacional"]} == {
        "Madrid",
        "Londres",
        "New York",
        "Buenos Aires",
        "Miami",
    }
