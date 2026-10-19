"""HU-002 · Inicio de sesión (CU-02) y control de acceso por rol (RNF-05, RF-34)."""

from app.bootstrap import MARCADOR, asegurar_root
from app.models import Rol, Usuario


def test_cliente_obtiene_token_con_su_rol(client, registrar):
    headers = registrar()
    yo = client.get("/auth/me", headers=headers).json()
    assert yo["rol"] == "CLIENTE"


def test_root_ingresa_con_su_id(client, root_headers):
    yo = client.get("/auth/me", headers=root_headers).json()
    assert yo["nombre_usuario"] == "root"
    assert yo["rol"] == "ROOT"


def test_administrador_ingresa_con_rol_administrador(client, admin_headers):
    assert client.get("/auth/me", headers=admin_headers).json()["rol"] == "ADMINISTRADOR"


def test_credenciales_invalidas_muestran_error_y_no_inician_sesion(client, registrar):
    registrar()
    for usuario, clave in [("analopez", "mala"), ("noexiste", "clave-segura")]:
        r = client.post("/auth/login", json={"nombre_usuario": usuario, "contrasena": clave})
        assert r.status_code == 401
        assert r.json()["detail"]["codigo"] == "CREDENCIALES_INVALIDAS"
        assert "access_token" not in r.text


def test_sin_token_o_token_falso_no_hay_sesion(client):
    assert client.get("/auth/me").status_code == 401
    r = client.get("/auth/me", headers={"Authorization": "Bearer token.falso.x"})
    assert r.status_code == 401
    assert r.json()["detail"]["codigo"] == "SESION_INVALIDA"


def test_cuenta_inactiva_no_inicia_sesion(client, db, registrar):
    registrar()
    db.query(Usuario).filter_by(nombre_usuario="analopez").one().activo = False
    db.commit()
    r = client.post("/auth/login", json={"nombre_usuario": "analopez", "contrasena": "clave-segura"})
    assert r.status_code == 401


def test_root_y_administrador_no_pueden_reservar_ni_comprar(client, root_headers, admin_headers):
    for headers in (root_headers, admin_headers):
        r = client.get("/reservas/acceso", headers=headers)
        assert r.status_code == 403
        assert r.json()["detail"]["codigo"] == "ROL_NO_PERMITIDO"


def test_cliente_si_puede_entrar_a_reservar(client, cliente_headers):
    r = client.get("/reservas/acceso", headers=cliente_headers)
    assert r.status_code == 200 and r.json()["permitido"] is True


def test_visitante_debe_iniciar_sesion_para_reservar(client):
    r = client.get("/reservas/acceso")
    assert r.status_code == 401
    assert r.json()["detail"]["codigo"] == "NO_AUTENTICADO"


def test_bootstrap_define_la_contrasena_del_root_una_sola_vez(client, db):
    root = db.query(Usuario).filter_by(rol=Rol.ROOT).one()
    assert root.contrasena_hash == MARCADOR  # el script del modelo deja el marcador
    r = client.post("/auth/login", json={"nombre_usuario": "root", "contrasena": MARCADOR})
    assert r.status_code == 401  # el marcador no sirve como contraseña

    assert asegurar_root(db, "inicial") is True
    assert asegurar_root(db, "otra") is False  # ya definida: no se sobrescribe
    assert (
        client.post("/auth/login", json={"nombre_usuario": "root", "contrasena": "inicial"}).status_code
        == 200
    )
