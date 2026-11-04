"""HU-015 Cancelar compra, HU-016 Cancelar reserva, HU-017 Histórico, HU-018 Liberación por vencimiento."""

from sqlalchemy import text

from tests.ayudas_compras import envejecer_reserva, mover_salida, reserva, viajero


def _comprar(client, headers, reservar, con_saldo, vuelo, *pasajeros):
    con_saldo("3000000")
    r = reservar(reserva(vuelo, *pasajeros))
    assert client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=headers).status_code == 201
    return r


# HU-015


def test_cancela_compra_dentro_del_plazo_con_reembolso_total(
    client, cliente_headers, reservar, con_saldo, vuelo
):
    antes = client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]["economica"]
    r = _comprar(
        client, cliente_headers, reservar, con_saldo, vuelo["codigo"], viajero("AAA1111"), viajero("BBB2222")
    )
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    assert c.status_code == 200, c.text
    assert c.json()["estado"] == "CANCELADA"
    assert float(c.json()["reembolso"]) == 560000
    m = client.get("/monedero", headers=cliente_headers).json()
    assert float(m["saldo"]) == 3000000
    assert any(x["tipo"] == "ABONO_REEMBOLSO" and r["codigo"] in x["descripcion"] for x in m["movimientos"])
    assert client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]["economica"] == antes


def test_nacional_no_se_cancela_a_menos_de_una_hora(client, db, cliente_headers, reservar, con_saldo, vuelo):
    r = _comprar(client, cliente_headers, reservar, con_saldo, vuelo["codigo"])
    mover_salida(db, vuelo["codigo"], 0.9)
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    assert c.status_code == 409 and c.json()["detail"]["codigo"] == "FUERA_DE_PLAZO"
    assert client.get(f"/reservas/{r['codigo']}", headers=cliente_headers).json()["puede_cancelar"] is False


def test_nacional_se_cancela_con_mas_de_una_hora(client, db, cliente_headers, reservar, con_saldo, vuelo):
    r = _comprar(client, cliente_headers, reservar, con_saldo, vuelo["codigo"])
    mover_salida(db, vuelo["codigo"], 1.2)
    assert client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers).status_code == 200


def test_internacional_tiene_plazo_de_tres_horas(client, db, cliente_headers, reservar, con_saldo, programar):
    v = programar(origen="PEI", destino="MAD")
    r = _comprar(client, cliente_headers, reservar, con_saldo, v["codigo"])
    mover_salida(db, v["codigo"], 2.5)
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    assert c.status_code == 409 and c.json()["detail"]["codigo"] == "FUERA_DE_PLAZO"
    mover_salida(db, v["codigo"], 3.5)
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    assert c.status_code == 200, c.text


def test_no_se_cancela_dos_veces(client, cliente_headers, reservar, con_saldo, vuelo):
    r = _comprar(client, cliente_headers, reservar, con_saldo, vuelo["codigo"])
    client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    assert c.status_code == 409 and c.json()["detail"]["codigo"] == "NO_CANCELABLE"
    m = client.get("/monedero", headers=cliente_headers).json()
    assert len([x for x in m["movimientos"] if x["tipo"] == "ABONO_REEMBOLSO"]) == 1


# HU-016


def test_cancela_reserva_vigente_y_libera_sillas(client, cliente_headers, reservar, vuelo):
    antes = client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]["economica"]
    r = reservar(reserva(vuelo["codigo"], viajero("AAA1111"), viajero("BBB2222")))
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers).json()
    assert c["estado"] == "CANCELADA" and c["reembolso"] is None
    assert {t["estado"] for t in c["tiquetes"]} == {"CANCELADO"}
    assert client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]["economica"] == antes
    assert client.get("/carrito", headers=cliente_headers).json()["reservas"] == []


def test_reserva_vencida_no_se_cancela(client, db, cliente_headers, reservar, vuelo):
    r = reservar(reserva(vuelo["codigo"]))
    envejecer_reserva(db, r["codigo"])
    c = client.post(f"/reservas/{r['codigo']}/cancelar", headers=cliente_headers)
    assert c.status_code == 409


# HU-017


def test_historico_lista_todas_y_muestra_el_detalle(
    client, db, cliente_headers, reservar, con_saldo, programar
):
    pagada = _comprar(client, cliente_headers, reservar, con_saldo, programar()["codigo"])
    cancelada = reservar(reserva(programar()["codigo"]))
    client.post(f"/reservas/{cancelada['codigo']}/cancelar", headers=cliente_headers)
    vencida = reservar(reserva(programar()["codigo"]))
    envejecer_reserva(db, vencida["codigo"])
    vigente = reservar(reserva(programar()["codigo"]))
    lista = client.get("/reservas", headers=cliente_headers).json()
    estados = {x["codigo"]: x["estado"] for x in lista}
    assert estados == {
        pagada["codigo"]: "PAGADA",
        cancelada["codigo"]: "CANCELADA",
        vencida["codigo"]: "VENCIDA",
        vigente["codigo"]: "RESERVADA",
    }
    assert lista[0]["codigo"] == vigente["codigo"]
    d = client.get(f"/reservas/{pagada['codigo']}", headers=cliente_headers).json()
    t = d["tiquetes"][0]
    for campo in ("silla", "posicion", "clase", "precio", "pasajero_nombre", "checkin", "salida_local"):
        assert t[campo] is not None, campo
    assert t["checkin"] == "PENDIENTE"


def test_historico_vacio(client, cliente_headers):
    assert client.get("/reservas", headers=cliente_headers).json() == []


# HU-018


def test_reserva_sin_pagar_se_libera_a_las_24_horas(client, db, cliente_headers, reservar, vuelo):
    antes = client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]["economica"]
    r = reservar(reserva(vuelo["codigo"], viajero("AAA1111"), viajero("BBB2222")))
    envejecer_reserva(db, r["codigo"], horas=24.1)
    assert client.get(f"/vuelos/{vuelo['codigo']}").json()["disponibles"]["economica"] == antes
    d = client.get(f"/reservas/{r['codigo']}", headers=cliente_headers).json()
    assert d["estado"] == "VENCIDA" and d["puede_pagar"] is False
    assert client.get("/carrito", headers=cliente_headers).json()["reservas"] == []
    pago = client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    assert pago.status_code == 409


def test_antes_de_24_horas_sigue_vigente(client, db, cliente_headers, reservar, vuelo):
    r = reservar(reserva(vuelo["codigo"]))
    envejecer_reserva(db, r["codigo"], horas=23.5)
    assert client.get(f"/reservas/{r['codigo']}", headers=cliente_headers).json()["estado"] == "RESERVADA"


def test_compras_pagadas_no_se_liberan(client, db, cliente_headers, reservar, con_saldo, vuelo):
    r = _comprar(client, cliente_headers, reservar, con_saldo, vuelo["codigo"])
    db.execute(
        text("UPDATE reserva SET fecha_creacion = now() - interval '3 days' WHERE codigo = :c"),
        {"c": r["codigo"]},
    )
    db.commit()
    assert client.get(f"/reservas/{r['codigo']}", headers=cliente_headers).json()["estado"] == "PAGADA"


def test_tarea_periodica_libera_vencidas(db, reservar, vuelo):
    from app.services.reservas import ahora, liberar_vencidas

    r = reservar(reserva(vuelo["codigo"]))
    envejecer_reserva(db, r["codigo"])
    assert liberar_vencidas(db, ahora()) == [r["codigo"]]
    assert liberar_vencidas(db, ahora()) == []
