"""HU-008 · Búsqueda de vuelos (CU-20, incluye CU-21)."""

import pytest
from sqlalchemy import text

from tests.ayudas_vuelos import vender_tiquete
from tests.conftest import manana


@pytest.fixture
def oferta(programar):
    """Cinco vuelos con rutas, fechas y precios distintos."""
    return {
        "pei_bog": programar(
            origen="PEI",
            destino="BOG",
            fecha_salida=manana(3),
            tarifa_economica="200000",
            tarifa_primera="500000",
        ),
        "pei_bog_2": programar(
            origen="PEI",
            destino="BOG",
            fecha_salida=manana(9),
            tarifa_economica="350000",
            tarifa_primera="800000",
        ),
        "pei_mde": programar(
            origen="PEI",
            destino="MDE",
            fecha_salida=manana(3),
            tarifa_economica="180000",
            tarifa_primera="400000",
        ),
        "bog_mad": programar(
            origen="BOG",
            destino="MAD",
            fecha_salida=manana(5),
            tarifa_economica="2900000",
            tarifa_primera="7000000",
        ),
        "clo_ctg": programar(
            origen="CLO",
            destino="CTG",
            fecha_salida=manana(12),
            tarifa_economica="260000",
            tarifa_primera="600000",
        ),
    }


def _codigos(client, **params):
    r = client.get("/vuelos/buscar", params=params)
    assert r.status_code == 200, r.text
    return [v["codigo"] for v in r.json()["vuelos"]]


def test_busqueda_principal_origen_destino_fecha_pasajeros(client, oferta):
    fecha = manana(3)
    codigos = _codigos(client, origen="PEI", destino="BOG", fecha_desde=fecha, fecha_hasta=fecha, pasajeros=2)
    assert codigos == [oferta["pei_bog"]["codigo"]]


def test_cada_filtro_funciona_solo(client, oferta):
    o = {k: v["codigo"] for k, v in oferta.items()}
    assert set(_codigos(client, origen="PEI")) == {o["pei_bog"], o["pei_bog_2"], o["pei_mde"]}
    assert set(_codigos(client, destino="BOG")) == {o["pei_bog"], o["pei_bog_2"]}
    assert set(_codigos(client, fecha_desde=manana(9))) == {o["pei_bog_2"], o["clo_ctg"]}
    assert set(_codigos(client, fecha_hasta=manana(4))) == {o["pei_bog"], o["pei_mde"]}
    assert set(_codigos(client, precio_min="1000000")) == {o["bog_mad"]}  # alguna tarifa ≥ 1 000 000
    assert set(_codigos(client, precio_max="190000")) == {o["pei_mde"]}
    assert len(_codigos(client, pasajeros=5)) == 5


def test_filtros_combinados(client, oferta):
    o = {k: v["codigo"] for k, v in oferta.items()}
    combinados = _codigos(
        client, origen="PEI", precio_max="300000", fecha_desde=manana(1), fecha_hasta=manana(10)
    )
    assert set(combinados) == {o["pei_bog"], o["pei_mde"]}
    # pei_bog: 200 000 / 500 000; pei_bog_2: 350 000 / 800 000. Solo el segundo tiene tarifa ≥ 600 000.
    assert _codigos(client, origen="PEI", destino="BOG", precio_min="600000") == [o["pei_bog_2"]]
    assert _codigos(client, origen="BOG", destino="MAD", fecha_desde=manana(6)) == []


def test_resultados_ordenados_por_salida(client, oferta):
    r = client.get("/vuelos/buscar").json()["vuelos"]
    salidas = [v["salida_utc"] for v in r]
    assert salidas == sorted(salidas)


def test_codigos_de_ciudad_sin_importar_mayusculas(client, oferta):
    assert _codigos(client, origen="pei", destino="bog") == _codigos(client, origen="PEI", destino="BOG")


def test_solo_vuelos_programados_y_futuros(client, db, oferta):
    db.execute(
        text("UPDATE vuelo SET estado = 'CANCELADO' WHERE codigo = :c"), {"c": oferta["pei_mde"]["codigo"]}
    )
    db.execute(
        text("UPDATE vuelo SET fecha_hora_salida = now() - interval '2 hours' WHERE codigo = :c"),
        {"c": oferta["clo_ctg"]["codigo"]},
    )
    db.commit()
    codigos = _codigos(client)
    assert oferta["pei_mde"]["codigo"] not in codigos
    assert oferta["clo_ctg"]["codigo"] not in codigos
    assert len(codigos) == 3


def test_pasajeros_considera_sillas_disponibles(client, db, registrar, oferta, programar):
    registrar()
    vuelo = oferta["pei_mde"]
    vender_tiquete(db, vuelo, silla=30)
    r = client.get(f"/vuelos/{vuelo['codigo']}").json()
    assert r["disponibles"] == {"primera": 25, "economica": 124}


def test_validacion_de_rangos_y_pasajeros(client):
    r = client.get("/vuelos/buscar", params={"fecha_desde": manana(5), "fecha_hasta": manana(1)})
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "RANGO_FECHAS_INVALIDO"
    r = client.get("/vuelos/buscar", params={"precio_min": "500", "precio_max": "100"})
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "RANGO_PRECIOS_INVALIDO"
    assert client.get("/vuelos/buscar", params={"pasajeros": 6}).status_code == 422
    assert client.get("/vuelos/buscar", params={"pasajeros": 0}).status_code == 422


def test_visitante_busca_sin_iniciar_sesion(client, oferta):
    assert client.get("/vuelos/buscar").json()["total"] == 5


def test_visitante_que_intenta_reservar_debe_identificarse(client, oferta):
    assert client.get("/reservas/acceso").status_code == 401


def test_las_busquedas_del_cliente_quedan_en_su_actividad(client, db, cliente_headers, oferta):
    client.get(
        "/vuelos/buscar", params={"origen": "PEI", "destino": "BOG", "pasajeros": 2}, headers=cliente_headers
    )
    client.get("/vuelos/buscar", params={"precio_max": "300000"}, headers=cliente_headers)
    actividad = client.get("/usuarios/me/actividad", headers=cliente_headers).json()
    assert len(actividad) == 2
    assert actividad[0]["tipo"] == "BUSQUEDA"
    reciente, anterior = actividad
    assert float(reciente["precio_max"]) == 300000
    assert (anterior["origen"], anterior["destino"], anterior["pasajeros"]) == ("PEI", "BOG", 2)


def test_busquedas_de_visitante_o_admin_no_se_registran(client, db, admin_headers, oferta):
    client.get("/vuelos/buscar", params={"origen": "PEI"})
    client.get("/vuelos/buscar", params={"origen": "PEI"}, headers=admin_headers)
    assert db.execute(text("SELECT count(*) FROM actividad_usuario")).scalar_one() == 0
