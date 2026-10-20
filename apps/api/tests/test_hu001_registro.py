"""HU-001 · Registro de cliente (CU-01)."""

import pytest
from sqlalchemy import text

from tests.conftest import datos_cliente, login


def test_registro_crea_cliente_con_monedero_y_carrito(client, db):
    r = client.post("/auth/registro", json=datos_cliente())
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["rol"] == "CLIENTE"
    assert cuerpo["perfil_completo"] is True
    assert cuerpo["perfil"]["documento"] == "1088123456"
    assert "contrasena" not in r.text

    uid = cuerpo["id"]
    assert db.execute(text("SELECT saldo FROM monedero WHERE cliente_id = :u"), {"u": uid}).scalar_one() == 0
    assert (
        db.execute(text("SELECT count(*) FROM carrito WHERE cliente_id = :u"), {"u": uid}).scalar_one() == 1
    )
    # La contraseña nunca se guarda en claro.
    guardada = db.execute(text("SELECT contrasena_hash FROM usuario WHERE id = :u"), {"u": uid}).scalar_one()
    assert guardada != "clave-segura" and guardada.startswith("$2")


def test_imagen_de_usuario_es_opcional(client):
    con = client.post("/auth/registro", json=datos_cliente(imagen_url="https://img.example/ana.png"))
    assert con.status_code == 201
    assert con.json()["perfil"]["imagen_url"] == "https://img.example/ana.png"
    sin = client.post(
        "/auth/registro",
        json=datos_cliente(documento="AB123456", tipo_documento="PASAPORTE", nombre_usuario="otro"),
    )
    assert sin.status_code == 201
    assert sin.json()["perfil"]["imagen_url"] is None


@pytest.mark.parametrize(
    "campo",
    [
        "documento",
        "tipo_documento",
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "lugar_nacimiento",
        "direccion_facturacion",
        "genero",
        "correo",
        "nombre_usuario",
        "contrasena",
    ],
)
def test_falta_dato_obligatorio_no_crea_cuenta_e_indica_que_corregir(client, db, campo):
    datos = datos_cliente()
    del datos[campo]
    r = client.post("/auth/registro", json=datos)
    assert r.status_code == 422
    detalle = r.json()["detail"]
    assert detalle["codigo"] == "DATOS_INVALIDOS"
    assert any(c["campo"] == campo for c in detalle["campos"])
    assert db.execute(text("SELECT count(*) FROM usuario WHERE rol = 'CLIENTE'")).scalar_one() == 0


def test_dato_obligatorio_en_blanco_no_crea_cuenta(client):
    r = client.post("/auth/registro", json=datos_cliente(nombres="   "))
    assert r.status_code == 422
    assert r.json()["detail"]["campos"][0]["campo"] == "nombres"


@pytest.mark.parametrize("documento", ["1088-123", "10 88 12", "ABC", "ñ1234567", "1234567890123456789012"])
def test_documento_no_alfanumerico_se_rechaza(client, documento):
    r = client.post("/auth/registro", json=datos_cliente(documento=documento))
    assert r.status_code == 422
    campo = r.json()["detail"]["campos"][0]
    assert campo["campo"] == "documento"
    assert "alfanumérico" in campo["mensaje"]


def test_pasaporte_alfanumerico_se_acepta(client):
    r = client.post("/auth/registro", json=datos_cliente(documento="PA12345X", tipo_documento="PASAPORTE"))
    assert r.status_code == 201


def test_documento_registrado_informa_que_la_cuenta_existe(client):
    assert client.post("/auth/registro", json=datos_cliente()).status_code == 201
    r = client.post("/auth/registro", json=datos_cliente(nombre_usuario="otrousuario"))
    assert r.status_code == 409
    detalle = r.json()["detail"]
    assert detalle["codigo"] == "DOCUMENTO_REGISTRADO"
    assert "Inicia sesión" in detalle["mensaje"]


def test_usuario_en_uso_pide_otro(client):
    assert client.post("/auth/registro", json=datos_cliente()).status_code == 201
    r = client.post("/auth/registro", json=datos_cliente(documento="99887766"))
    assert r.status_code == 409
    assert r.json()["detail"]["codigo"] == "USUARIO_EN_USO"
    assert r.json()["detail"]["campos"][0]["campo"] == "nombre_usuario"


def test_correo_invalido_y_fecha_futura_se_rechazan(client):
    r = client.post(
        "/auth/registro", json=datos_cliente(correo="no-es-correo", fecha_nacimiento="2999-01-01")
    )
    assert r.status_code == 422
    campos = {c["campo"] for c in r.json()["detail"]["campos"]}
    assert campos == {"correo", "fecha_nacimiento"}


def test_despues_del_registro_el_cliente_inicia_sesion(client):
    client.post("/auth/registro", json=datos_cliente())
    headers = login(client, "analopez", "clave-segura")
    yo = client.get("/auth/me", headers=headers)
    assert yo.status_code == 200
    assert yo.json()["nombre_usuario"] == "analopez"
    assert yo.json()["rol"] == "CLIENTE"
