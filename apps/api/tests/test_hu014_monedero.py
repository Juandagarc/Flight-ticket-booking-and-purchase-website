"""HU-014 Gestión del monedero (CU-36)."""

from sqlalchemy import text

TARJETA = {
    "tipo": "CREDITO",
    "franquicia": "VISA",
    "titular": "ANA MARIA LOPEZ",
    "numero": "4111111111111111",
    "vencimiento": "12/30",
}


def test_monedero_nuevo_en_cero(client, cliente_headers):
    m = client.get("/monedero", headers=cliente_headers).json()
    assert float(m["saldo"]) == 0
    assert m["tarjetas"] == [] and m["movimientos"] == []


def test_tarjeta_guarda_solo_los_ultimos_cuatro_digitos(client, db, cliente_headers):
    r = client.post("/monedero/tarjetas", json=TARJETA, headers=cliente_headers)
    assert r.status_code == 201
    assert r.json()["ultimos_digitos"] == "1111"
    assert "numero" not in r.json()
    fila = db.execute(text("SELECT row_to_json(t)::text FROM tarjeta t")).scalar()
    assert "4111111111111111" not in fila


def test_tarjeta_invalida(client, cliente_headers):
    for cambio in (
        {"numero": "4111111111111112"},
        {"vencimiento": "01/20"},
        {"franquicia": "OTRA"},
        {"numero": "12ab"},
    ):
        r = client.post("/monedero/tarjetas", json={**TARJETA, **cambio}, headers=cliente_headers)
        assert r.status_code == 422, cambio


def test_quitar_tarjeta(client, cliente_headers, registrar):
    t = client.post("/monedero/tarjetas", json=TARJETA, headers=cliente_headers).json()
    ajeno = registrar(documento="99887766", nombre_usuario="pedro", correo="pedro@example.com")
    assert client.delete(f"/monedero/tarjetas/{t['id']}", headers=ajeno).status_code == 404
    assert client.delete(f"/monedero/tarjetas/{t['id']}", headers=cliente_headers).status_code == 204
    assert client.get("/monedero", headers=cliente_headers).json()["tarjetas"] == []


def test_ajuste_manual_queda_como_movimiento(client, cliente_headers, con_saldo):
    con_saldo("300000")
    m = con_saldo("250000")
    assert float(m["saldo"]) == 250000
    ajustes = [m for m in m["movimientos"] if m["tipo"] == "AJUSTE_MANUAL"]
    assert sorted(float(a["monto"]) for a in ajustes) == [-50000, 300000]
    assert client.put("/monedero/saldo", json={"saldo": "250000"}, headers=cliente_headers).status_code == 422
    assert client.put("/monedero/saldo", json={"saldo": "-1"}, headers=cliente_headers).status_code == 422


def test_solo_cliente(client, admin_headers, root_headers):
    for h in (admin_headers, root_headers):
        assert client.get("/monedero", headers=h).status_code == 403
