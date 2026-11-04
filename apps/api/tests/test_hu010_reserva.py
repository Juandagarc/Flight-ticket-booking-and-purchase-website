"""HU-010 · Reserva de tiquetes (CU-22, incluye CU-23 y CU-24)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from tests.ayudas_compras import mover_salida, reserva, viajero
from tests.conftest import manana


def test_pide_los_datos_de_cada_viajero(client, cliente_headers, vuelo):
    for campo in [
        "documento",
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "genero",
        "telefono",
        "correo",
        "nombre_contacto",
        "telefono_contacto",
    ]:
        datos = viajero()
        del datos[campo]
        r = client.post("/reservas", json=reserva(vuelo["codigo"], datos), headers=cliente_headers)
        assert r.status_code == 422, campo
        assert any(c["campo"].endswith(campo) for c in r.json()["detail"]["campos"]), campo


def test_reserva_sin_pagar_bloquea_sillas_y_vence_a_las_24_horas(client, reservar, vuelo):
    antes = client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]
    r = reservar(reserva(vuelo["codigo"], viajero("AAA1111"), viajero("BBB2222")))
    assert r["estado"] == "RESERVADA"
    assert len(r["codigo"]) == 6
    assert r["en_carrito"] is True
    assert r["puede_pagar"] is True
    vence = datetime.fromisoformat(r["fecha_expiracion"])
    creada = datetime.fromisoformat(r["fecha_creacion"])
    assert abs((vence - creada) - timedelta(hours=24)) < timedelta(seconds=5)
    despues = client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]
    assert despues["economica"] == antes["economica"] - 2
    assert despues["primera"] == antes["primera"]
    assert float(r["total"]) == 2 * 280000


def test_cada_viajero_recibe_una_silla_aleatoria_de_la_clase(client, reservar, vuelo):
    r = reservar(reserva(vuelo["codigo"], viajero("AAA1111"), viajero("BBB2222"), clase="PRIMERA"))
    sillas = [t["silla"] for t in r["tiquetes"]]
    assert len(set(sillas)) == 2
    assert all(1 <= s <= 25 for s in sillas)  # RF-43: 1 a 25 es primera clase en nacionales
    assert {t["clase"] for t in r["tiquetes"]} == {"PRIMERA"}
    assert all(t["posicion"] in {"VENTANA", "CENTRO", "PASILLO"} for t in r["tiquetes"])
    economica = reservar(reserva(vuelo["codigo"], viajero("CCC3333")))
    assert 26 <= economica["tiquetes"][0]["silla"] <= 150


def test_reserva_para_terceros(reservar, vuelo):
    r = reservar(reserva(vuelo["codigo"], viajero("ABUELO01", nombres="Rosa", fecha_nacimiento="1950-02-01")))
    assert r["tiquetes"][0]["pasajero_nombre"].startswith("Rosa")


def test_no_acepta_sexto_tiquete_del_cliente_en_el_vuelo(client, cliente_headers, reservar, vuelo):
    reservar(reserva(vuelo["codigo"], *[viajero(f"DOC{i:05d}") for i in range(3)]))
    reservar(reserva(vuelo["codigo"], *[viajero(f"DOC{i:05d}") for i in range(3, 5)]))
    r = client.post("/reservas", json=reserva(vuelo["codigo"], viajero("DOC00099")), headers=cliente_headers)
    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "TOPE_TIQUETES"
    seis = reserva(vuelo["codigo"], *[viajero(f"X{i:05d}") for i in range(6)])
    assert client.post("/reservas", json=seis, headers=cliente_headers).status_code == 422


def test_tiquetes_cancelados_no_cuentan_para_el_tope(client, cliente_headers, reservar, vuelo):
    r = reservar(reserva(vuelo["codigo"], *[viajero(f"DOC{i:05d}") for i in range(5)]))
    client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    reservar(reserva(vuelo["codigo"], viajero("NUEVO001")))


def test_no_acepta_viajero_repetido_en_el_mismo_vuelo(client, cliente_headers, reservar, registrar, vuelo):
    r = client.post(
        "/reservas",
        json=reserva(vuelo["codigo"], viajero("AAA1111"), viajero("AAA1111")),
        headers=cliente_headers,
    )
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "PASAJERO_REPETIDO"
    reservar(reserva(vuelo["codigo"], viajero("AAA1111")))
    otro = registrar(documento="99887766", nombre_usuario="pedro", correo="pedro@example.com")
    r = client.post("/reservas", json=reserva(vuelo["codigo"], viajero("AAA1111")), headers=otro)
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "PASAJERO_REPETIDO"


def test_menor_no_viaja_solo(client, cliente_headers, reservar, vuelo):
    nino = viajero(
        "NINO0001", fecha_nacimiento=(datetime.now(UTC).date() - timedelta(days=8 * 365)).isoformat()
    )
    r = client.post("/reservas", json=reserva(vuelo["codigo"], nino), headers=cliente_headers)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "MENOR_SOLO"
    reservar(reserva(vuelo["codigo"], nino, viajero("ADULTO01")))


def test_sin_sillas_suficientes_en_la_clase(client, db, cliente_headers, root_headers, vuelo):
    db.execute(
        text("""
        INSERT INTO pasajero (documento, nombres, apellidos, fecha_nacimiento, genero, telefono, correo,
                              nombre_contacto, telefono_contacto)
        SELECT 'LLENO' || n, 'X', 'Y', '1980-01-01', 'OTRO', '3000000000', 'x@example.com', 'Z', '3000000000'
        FROM generate_series(1, 24) n""")
    )
    db.execute(
        text("""
        INSERT INTO reserva (codigo, cliente_id, estado, tipo_trayecto, fecha_expiracion)
        VALUES ('LLENO1', (SELECT id FROM usuario WHERE nombre_usuario <> 'analopez' LIMIT 1), 'RESERVADA', 'SENCILLO', now() + interval '1 day')""")
    )
    db.execute(
        text("""
        INSERT INTO tiquete (reserva_codigo, vuelo_codigo, tipo_vuelo, pasajero_documento, silla_numero, clase, precio)
        SELECT 'LLENO1', :v, 'NACIONAL', 'LLENO' || n, n, 'PRIMERA', 1 FROM generate_series(1, 24) n"""),
        {"v": vuelo["codigo"]},
    )
    db.commit()
    r = client.post(
        "/reservas",
        json=reserva(vuelo["codigo"], viajero("A0000001"), viajero("A0000002"), clase="PRIMERA"),
        headers=cliente_headers,
    )
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "SIN_SILLAS"


def test_ida_y_vuelta_es_una_reserva_con_un_tiquete_por_tramo(client, reservar, programar):
    ida = programar(origen="PEI", destino="CTG", fecha_salida=manana(5))
    regreso = programar(origen="CTG", destino="PEI", fecha_salida=manana(9))
    opciones = client.get(f"/vuelos/{ida['codigo']}/regresos").json()
    assert [v["codigo"] for v in opciones] == [regreso["codigo"]]
    r = reservar(reserva(ida["codigo"], viajero("AAA1111"), viajero("BBB2222"), regreso=regreso["codigo"]))
    assert r["tipo_trayecto"] == "IDA_Y_VUELTA"
    assert [t["vuelo_codigo"] for t in r["tramos"]] == [ida["codigo"], regreso["codigo"]]
    assert len(r["tiquetes"]) == 4
    assert float(r["total"]) == 4 * 280000


@pytest.mark.parametrize(
    ("ida", "vuelta"),
    [
        (
            {"origen": "PEI", "destino": "CTG", "fecha_salida": manana(9)},
            {"origen": "CTG", "destino": "PEI", "fecha_salida": manana(5)},
        ),  # sale antes de llegar
        (
            {"origen": "PEI", "destino": "CTG", "fecha_salida": manana(5)},
            {"origen": "CTG", "destino": "BOG", "fecha_salida": manana(9)},
        ),  # no vuelve al origen
    ],
)
def test_regreso_invalido(client, cliente_headers, programar, ida, vuelta):
    a = programar(**ida)
    b = programar(**vuelta)
    r = client.post("/reservas", json=reserva(a["codigo"], regreso=b["codigo"]), headers=cliente_headers)
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "REGRESO_INVALIDO"


def test_vuelo_pasado_o_cancelado_no_se_reserva(client, db, cliente_headers, vuelo):
    db.execute(text("UPDATE vuelo SET estado = 'CANCELADO' WHERE codigo = :c"), {"c": vuelo["codigo"]})
    db.commit()
    r = client.post("/reservas", json=reserva(vuelo["codigo"]), headers=cliente_headers)
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "VUELO_NO_DISPONIBLE"


def test_vence_antes_si_el_vuelo_sale_en_menos_de_24_horas(db, reservar, vuelo):
    mover_salida(db, vuelo["codigo"], 6)
    res = reservar(reserva(vuelo["codigo"]))
    vence = datetime.fromisoformat(res["fecha_expiracion"])
    assert vence - datetime.now(UTC) < timedelta(hours=6, minutes=1)


def test_reserva_queda_en_la_actividad_del_cliente(client, cliente_headers, reservar, vuelo):
    reservar(reserva(vuelo["codigo"]))
    tipos = [a["tipo"] for a in client.get("/usuarios/me/actividad", headers=cliente_headers).json()]
    assert "RESERVA" in tipos


def test_solo_el_cliente_reserva(client, root_headers, admin_headers, vuelo):
    for headers in (root_headers, admin_headers, {}):
        assert client.post("/reservas", json=reserva(vuelo["codigo"]), headers=headers).status_code in (
            401,
            403,
        )


def test_viajero_que_es_cliente_registrado_queda_enlazado(client, db, reservar, vuelo):
    reservar(reserva(vuelo["codigo"], viajero("1088123456")))  # documento del cliente «analopez»
    enlazado = db.execute(
        text("SELECT cliente_id IS NOT NULL FROM pasajero WHERE documento = '1088123456'")
    ).scalar()
    assert enlazado is True
