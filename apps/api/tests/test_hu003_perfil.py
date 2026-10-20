"""HU-003 · Gestión del perfil (CU-03)."""

from tests.conftest import ADMIN_PASS, datos_cliente, login

EDITABLES = {
    "nombres": "Ana Lucía",
    "apellidos": "López Restrepo",
    "fecha_nacimiento": "1995-04-12",
    "lugar_nacimiento": "Manizales",
    "direccion_facturacion": "Carrera 7 # 19-40, Pereira",
    "genero": "FEMENINO",
    "correo": "ana.lucia@example.com",
}


def test_cliente_consulta_su_perfil(client, cliente_headers):
    r = client.get("/usuarios/me/perfil", headers=cliente_headers)
    assert r.status_code == 200
    assert r.json()["nombres"] == "Ana María"


def test_cambios_validos_quedan_guardados_al_volver_a_ingresar(client, cliente_headers):
    r = client.put("/usuarios/me/perfil", json=EDITABLES, headers=cliente_headers)
    assert r.status_code == 200
    # Nuevo inicio de sesión: los cambios persisten.
    headers = login(client, "analopez", "clave-segura")
    perfil = client.get("/usuarios/me/perfil", headers=headers).json()
    assert perfil["nombres"] == "Ana Lucía"
    assert perfil["lugar_nacimiento"] == "Manizales"
    assert perfil["correo"] == "ana.lucia@example.com"
    assert perfil["documento"] == "1088123456"


def test_no_se_guarda_si_un_dato_obligatorio_queda_en_blanco(client, cliente_headers):
    r = client.put("/usuarios/me/perfil", json={**EDITABLES, "apellidos": ""}, headers=cliente_headers)
    assert r.status_code == 422
    assert r.json()["detail"]["campos"][0]["campo"] == "apellidos"
    perfil = client.get("/usuarios/me/perfil", headers=cliente_headers).json()
    assert perfil["apellidos"] == "López Restrepo"


def test_el_documento_no_se_edita(client, cliente_headers):
    r = client.put(
        "/usuarios/me/perfil", json={**EDITABLES, "documento": "00000000"}, headers=cliente_headers
    )
    assert r.status_code == 422
    assert r.json()["detail"]["campos"][0]["campo"] == "documento"
    assert client.get("/usuarios/me/perfil", headers=cliente_headers).json()["documento"] == "1088123456"


def test_administrador_completa_su_registro_con_los_campos_de_cliente(client, admin_headers):
    assert client.get("/usuarios/me/perfil", headers=admin_headers).status_code == 404
    datos = {
        k: v
        for k, v in datos_cliente(documento="75000111").items()
        if k not in ("nombre_usuario", "contrasena")
    }
    r = client.post("/usuarios/me/perfil", json=datos, headers=admin_headers)
    assert r.status_code == 201
    assert client.get("/auth/me", headers=admin_headers).json()["perfil_completo"] is True
    # Y luego lo puede editar como un cliente.
    assert client.put("/usuarios/me/perfil", json=EDITABLES, headers=admin_headers).status_code == 200


def test_completar_perfil_no_habilita_compras_al_administrador(client, admin_headers):
    datos = {
        k: v
        for k, v in datos_cliente(documento="75000111").items()
        if k not in ("nombre_usuario", "contrasena")
    }
    client.post("/usuarios/me/perfil", json=datos, headers=admin_headers)
    headers = login(client, "admin1", ADMIN_PASS)
    assert client.get("/reservas/acceso", headers=headers).status_code == 403


def test_administrador_no_usa_documento_de_otra_cuenta(client, admin_headers, cliente_headers):
    datos = {k: v for k, v in datos_cliente().items() if k not in ("nombre_usuario", "contrasena")}
    r = client.post("/usuarios/me/perfil", json=datos, headers=admin_headers)
    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "DOCUMENTO_REGISTRADO"


def test_root_no_tiene_perfil(client, root_headers):
    assert client.get("/usuarios/me/perfil", headers=root_headers).status_code == 403
    assert client.put("/usuarios/me/perfil", json=EDITABLES, headers=root_headers).status_code == 403


def test_visitante_no_accede_al_perfil(client):
    assert client.get("/usuarios/me/perfil").status_code == 401
