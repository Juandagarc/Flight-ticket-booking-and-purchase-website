"""HU-005 · Creación de administradores (CU-05)."""

from tests.conftest import datos_vuelo, login


def test_solo_el_root_ve_y_usa_la_opcion(client, root_headers, admin_headers, cliente_headers):
    nuevo = {"nombre_usuario": "operaciones", "contrasena": "inicial123"}
    for headers in (admin_headers, cliente_headers, {}):
        assert client.get("/administradores", headers=headers).status_code in (401, 403)
        assert client.post("/administradores", json=nuevo, headers=headers).status_code in (401, 403)
    assert client.get("/administradores", headers=root_headers).status_code == 200
    assert client.post("/administradores", json=nuevo, headers=root_headers).status_code == 201


def test_no_se_crea_administrador_con_usuario_existente(client, root_headers, registrar):
    registrar()  # cliente «analopez»
    for usuario in ("analopez", "root"):
        r = client.post(
            "/administradores", json={"nombre_usuario": usuario, "contrasena": "x1"}, headers=root_headers
        )
        assert r.status_code == 409
        assert r.json()["detail"]["codigo"] == "USUARIO_EN_USO"
    client.post("/administradores", json={"nombre_usuario": "ops", "contrasena": "x1"}, headers=root_headers)
    r = client.post(
        "/administradores", json={"nombre_usuario": "ops", "contrasena": "x2"}, headers=root_headers
    )
    assert r.status_code == 409


def test_administrador_creado_gestiona_vuelos_pero_no_compra(client, root_headers):
    r = client.post(
        "/administradores", json={"nombre_usuario": "ops", "contrasena": "inicial123"}, headers=root_headers
    )
    assert r.json()["rol"] == "ADMINISTRADOR"
    headers = login(client, "ops", "inicial123")
    assert client.get("/vuelos/gestion", headers=headers).status_code == 200
    assert client.post("/vuelos", json=datos_vuelo(), headers=headers).status_code == 201
    assert client.get("/reservas/acceso", headers=headers).status_code == 403


def test_listado_muestra_los_administradores_creados(client, root_headers):
    client.post("/administradores", json={"nombre_usuario": "ops", "contrasena": "x"}, headers=root_headers)
    nombres = [a["nombre_usuario"] for a in client.get("/administradores", headers=root_headers).json()]
    assert nombres == ["ops"]
