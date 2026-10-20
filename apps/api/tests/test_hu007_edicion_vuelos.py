"""HU-007 · Edición de vuelos (CU-08)."""

from sqlalchemy import text

from tests.ayudas_vuelos import vender_tiquete
from tests.conftest import manana


def test_vuelo_con_tiquetes_vendidos_no_se_edita(client, db, admin_headers, cliente_headers, programar):
    vuelo = programar()
    assert vuelo["editable"] is True
    vender_tiquete(db, vuelo, estado="RESERVADA")  # una reserva bloquea la silla igual que una compra
    assert client.get(f"/vuelos/{vuelo['codigo']}").json()["editable"] is False
    r = client.put(f"/vuelos/{vuelo['codigo']}", json={"tarifa_economica": "300000"}, headers=admin_headers)
    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "VUELO_NO_EDITABLE"


def test_tiquetes_de_reservas_canceladas_no_bloquean(client, db, admin_headers, cliente_headers, programar):
    vuelo = programar()
    vender_tiquete(db, vuelo, estado="CANCELADA")
    r = client.put(f"/vuelos/{vuelo['codigo']}", json={"tarifa_economica": "300000"}, headers=admin_headers)
    assert r.status_code == 200


def test_vuelo_que_ya_ocurrio_no_se_edita(client, db, admin_headers, programar):
    vuelo = programar()
    db.execute(
        text("UPDATE vuelo SET fecha_hora_salida = now() - interval '1 hour' WHERE codigo = :c"),
        {"c": vuelo["codigo"]},
    )
    db.commit()
    r = client.put(f"/vuelos/{vuelo['codigo']}", json={"hora_salida": "10:00"}, headers=admin_headers)
    assert r.status_code == 409


def test_vuelo_cancelado_no_se_edita(client, db, admin_headers, programar):
    vuelo = programar()
    db.execute(text("UPDATE vuelo SET estado = 'CANCELADO' WHERE codigo = :c"), {"c": vuelo["codigo"]})
    db.commit()
    assert (
        client.put(
            f"/vuelos/{vuelo['codigo']}", json={"hora_salida": "10:00"}, headers=admin_headers
        ).status_code
        == 409
    )


def test_cambiar_ruta_u_hora_recalcula_tiempo_y_llegada(client, admin_headers, programar):
    vuelo = programar(origen="PEI", destino="BOG", hora_salida="08:30")
    r = client.put(
        f"/vuelos/{vuelo['codigo']}", json={"destino": "NYC", "hora_salida": "23:15"}, headers=admin_headers
    )
    assert r.status_code == 200
    editado = r.json()
    assert editado["codigo"] == vuelo["codigo"]
    assert editado["tipo"] == "INTERNACIONAL"
    assert editado["duracion_min"] > vuelo["duracion_min"]
    assert editado["salida_local"].endswith("T23:15:00")
    assert editado["llegada_local"] != vuelo["llegada_local"]
    assert editado["imagen_url"] == "/destinos/NYC.svg"
    assert editado["disponibles"]["primera"] == 50


def test_editar_solo_tarifas_conserva_horario(client, admin_headers, programar):
    vuelo = programar()
    r = client.put(f"/vuelos/{vuelo['codigo']}", json={"tarifa_primera": "700000"}, headers=admin_headers)
    editado = r.json()
    assert float(editado["tarifas"]["primera"]) == 700000
    assert editado["salida_local"] == vuelo["salida_local"]
    assert editado["duracion_min"] == vuelo["duracion_min"]


def test_edicion_aplica_las_mismas_validaciones_de_ruta(client, admin_headers, programar):
    vuelo = programar()
    assert (
        client.put(f"/vuelos/{vuelo['codigo']}", json={"destino": "PEI"}, headers=admin_headers).status_code
        == 422
    )
    assert (
        client.put(
            f"/vuelos/{vuelo['codigo']}", json={"destino": "MAD", "origen": "BGA"}, headers=admin_headers
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/vuelos/{vuelo['codigo']}", json={"fecha_salida": "2020-01-01"}, headers=admin_headers
        ).status_code
        == 422
    )


def test_cambios_guardados_se_ven_en_la_busqueda_y_noticias(client, admin_headers, programar):
    vuelo = programar(origen="PEI", destino="BOG")
    nueva_fecha = manana(20)
    client.put(
        f"/vuelos/{vuelo['codigo']}",
        json={"destino": "CLO", "fecha_salida": nueva_fecha, "tarifa_economica": "150000"},
        headers=admin_headers,
    )
    assert client.get("/vuelos/buscar", params={"origen": "PEI", "destino": "BOG"}).json()["total"] == 0
    encontrados = client.get(
        "/vuelos/buscar", params={"origen": "PEI", "destino": "CLO", "fecha_desde": nueva_fecha}
    ).json()["vuelos"]
    assert [v["codigo"] for v in encontrados] == [vuelo["codigo"]]
    assert float(encontrados[0]["tarifas"]["economica"]) == 150000
    noticia = client.get("/noticias").json()[0]
    assert noticia["destino"]["nombre"] == "Cali"
    assert "Cali" in noticia["titulo"]
    assert float(noticia["precio_unitario"]) == 150000


def test_solo_administrador_edita(client, root_headers, cliente_headers, programar):
    vuelo = programar()
    for headers in (root_headers, cliente_headers, {}):
        r = client.put(f"/vuelos/{vuelo['codigo']}", json={"hora_salida": "10:00"}, headers=headers)
        assert r.status_code in (401, 403)


def test_vuelo_inexistente(client, admin_headers):
    assert (
        client.put("/vuelos/FL9999", json={"hora_salida": "10:00"}, headers=admin_headers).status_code == 404
    )
