"""HU-012 Carrito multivuelo (CU-25)."""

from tests.ayudas_compras import reserva, viajero


def test_carrito_vacio(client, cliente_headers):
    c = client.get("/carrito", headers=cliente_headers).json()
    assert c["reservas"] == []
    assert float(c["total"]) == 0


def test_muestra_subtotales_y_total(client, cliente_headers, reservar, programar):
    reservar(reserva(programar()["codigo"], viajero("AAA1111"), viajero("BBB2222")))
    reservar(reserva(programar()["codigo"], clase="PRIMERA"))
    c = client.get("/carrito", headers=cliente_headers).json()
    assert len(c["reservas"]) == 2
    subtotales = sorted(float(t["subtotal"]) for r in c["reservas"] for t in r["tramos"])
    assert subtotales == [560000, 650000]
    assert float(c["total"]) == 560000 + 650000


def test_retirar_actualiza_el_total_y_la_reserva_sigue_vigente(client, cliente_headers, reservar, programar):
    a = reservar(reserva(programar()["codigo"]))
    reservar(reserva(programar()["codigo"], clase="PRIMERA"))
    c = client.delete(f"/carrito/{a['codigo']}", headers=cliente_headers).json()
    assert float(c["total"]) == 650000
    assert client.get(f"/reservas/{a['codigo']}", headers=cliente_headers).json()["estado"] == "RESERVADA"
    c = client.post(f"/carrito/{a['codigo']}", headers=cliente_headers).json()
    assert float(c["total"]) == 650000 + 280000


def test_gestionar_el_carrito_no_toca_el_saldo(client, cliente_headers, reservar, con_saldo, vuelo):
    con_saldo("750000")
    r = reservar(reserva(vuelo["codigo"]))
    client.delete(f"/carrito/{r['codigo']}", headers=cliente_headers)
    client.post(f"/carrito/{r['codigo']}", headers=cliente_headers)
    c = client.get("/carrito", headers=cliente_headers).json()
    assert float(c["saldo"]) == 750000


def test_ida_y_vuelta_es_un_solo_item(client, cliente_headers, reservar, programar):
    from tests.conftest import manana

    ida = programar(origen="PEI", destino="CTG", fecha_salida=manana(5))
    vuelta = programar(origen="CTG", destino="PEI", fecha_salida=manana(8))
    reservar(reserva(ida["codigo"], regreso=vuelta["codigo"]))
    c = client.get("/carrito", headers=cliente_headers).json()
    assert len(c["reservas"]) == 1 and len(c["reservas"][0]["tramos"]) == 2


def test_solo_cliente(client, admin_headers):
    assert client.get("/carrito", headers=admin_headers).status_code == 403
    assert client.get("/carrito").status_code == 401
