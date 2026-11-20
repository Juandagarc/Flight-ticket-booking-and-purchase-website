"""HU-011 Compra de tiquetes (CU-26) y HU-013 Pago con monedero (CU-37)."""

from sqlalchemy import text

from tests.ayudas_compras import reserva, viajero


def test_compra_genera_codigo_y_lo_envia_a_cada_viajero(
    client, cliente_headers, reservar, con_saldo, buzon, vuelo
):
    con_saldo("1000000")
    r = reservar(reserva(vuelo["codigo"], viajero("AAA1111"), viajero("BBB2222")))
    pago = client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    assert pago.status_code == 201, pago.text
    assert float(pago.json()["monto_total"]) == 560000
    assert float(pago.json()["saldo"]) == 440000
    destinos = {m.para for m in buzon.enviados if r["codigo"] in m.cuerpo}
    assert destinos == {"aaa1111@example.com", "bbb2222@example.com"}
    detalle = client.get(f"/reservas/{r['codigo']}", headers=cliente_headers).json()
    assert detalle["estado"] == "PAGADA"
    assert detalle["en_carrito"] is False
    assert detalle["pago_fecha"] is not None


def test_codigos_de_reserva_son_unicos(reservar, programar):
    codigos = set()
    for i in range(8):
        v = programar()
        codigos.add(reservar(reserva(v["codigo"], viajero(f"U{i:06d}")))["codigo"])
    assert len(codigos) == 8


def test_pago_debita_el_monedero_con_referencia(client, cliente_headers, reservar, con_saldo, vuelo):
    con_saldo("500000")
    r = reservar(reserva(vuelo["codigo"]))
    client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    movimientos = client.get("/monedero", headers=cliente_headers).json()["movimientos"]
    debito = next(m for m in movimientos if m["tipo"] == "DEBITO_COMPRA")
    assert float(debito["monto"]) == -280000
    assert r["codigo"] in debito["descripcion"]
    assert float(debito["saldo_resultante"]) == 220000


def test_saldo_insuficiente_rechaza_sin_debitar_ni_comprar(
    client, cliente_headers, reservar, con_saldo, buzon, vuelo
):
    con_saldo("100000")
    r = reservar(reserva(vuelo["codigo"]))
    enviados = len(buzon.enviados)
    pago = client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    assert pago.status_code == 402
    assert pago.json()["detail"]["codigo"] == "SALDO_INSUFICIENTE"
    monedero = client.get("/monedero", headers=cliente_headers).json()
    assert float(monedero["saldo"]) == 100000
    assert not any(m["tipo"] == "DEBITO_COMPRA" for m in monedero["movimientos"])
    assert client.get(f"/reservas/{r['codigo']}", headers=cliente_headers).json()["estado"] == "RESERVADA"
    assert len(buzon.enviados) == enviados


def test_paga_varias_reservas_del_carrito_en_una_transaccion(
    client, cliente_headers, reservar, con_saldo, programar
):
    con_saldo("2000000")
    a = reservar(reserva(programar()["codigo"]))
    b = reservar(reserva(programar()["codigo"], clase="PRIMERA"))
    pago = client.post(
        "/pagos", json={"reservas": [a["codigo"], b["codigo"]]}, headers=cliente_headers
    ).json()
    assert float(pago["monto_total"]) == 280000 + 650000
    assert client.get("/carrito", headers=cliente_headers).json()["reservas"] == []


def test_no_se_paga_dos_veces_ni_una_reserva_ajena(
    client, cliente_headers, reservar, con_saldo, registrar, vuelo
):
    con_saldo("1000000")
    r = reservar(reserva(vuelo["codigo"]))
    client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    otra = client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    assert otra.status_code == 409 and otra.json()["detail"]["codigo"] == "RESERVA_NO_PAGABLE"
    ajeno = registrar(documento="99887766", nombre_usuario="pedro", correo="pedro@example.com")
    assert client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=ajeno).status_code == 404
    assert client.get(f"/reservas/{r['codigo']}", headers=ajeno).status_code == 404


def test_no_se_paga_si_el_vuelo_ya_no_esta_a_la_venta(
    client, db, cliente_headers, reservar, con_saldo, vuelo
):
    con_saldo("1000000")
    r = reservar(reserva(vuelo["codigo"]))
    db.execute(text("UPDATE vuelo SET estado = 'CANCELADO' WHERE codigo = :c"), {"c": vuelo["codigo"]})
    db.commit()
    pago = client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    assert pago.status_code == 409
    assert float(client.get("/monedero", headers=cliente_headers).json()["saldo"]) == 1000000


def test_compra_queda_en_la_actividad(client, cliente_headers, reservar, con_saldo, vuelo):
    con_saldo("1000000")
    r = reservar(reserva(vuelo["codigo"]))
    client.post("/pagos", json={"reservas": [r["codigo"]]}, headers=cliente_headers)
    tipos = [a["tipo"] for a in client.get("/usuarios/me/actividad", headers=cliente_headers).json()]
    assert "COMPRA" in tipos
