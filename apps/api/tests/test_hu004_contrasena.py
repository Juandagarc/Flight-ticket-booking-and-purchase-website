"""HU-004 · Cambio de contraseña (CU-04)."""

import pytest

from tests.conftest import ADMIN_PASS, ROOT_PASS


def _cambiar(client, headers, actual, nueva, confirmacion=None):
    return client.put(
        "/usuarios/me/contrasena",
        json={"actual": actual, "nueva": nueva, "confirmacion": confirmacion or nueva},
        headers=headers,
    )


def _login(client, usuario, clave):
    return client.post("/auth/login", json={"nombre_usuario": usuario, "contrasena": clave}).status_code


def test_contrasena_actual_incorrecta_se_rechaza(client, cliente_headers):
    r = _cambiar(client, cliente_headers, "equivocada", "nueva-clave")
    assert r.status_code == 400
    assert r.json()["detail"]["codigo"] == "CONTRASENA_ACTUAL_INCORRECTA"
    assert _login(client, "analopez", "clave-segura") == 200


def test_confirmacion_distinta_se_indica(client, cliente_headers):
    r = _cambiar(client, cliente_headers, "clave-segura", "nueva-clave", "otra-clave")
    assert r.status_code == 400
    assert r.json()["detail"]["codigo"] == "CONFIRMACION_NO_COINCIDE"
    assert _login(client, "analopez", "nueva-clave") == 401


@pytest.mark.parametrize(
    ("fixture", "usuario", "actual"),
    [
        ("cliente_headers", "analopez", "clave-segura"),
        ("admin_headers", "admin1", ADMIN_PASS),
        ("root_headers", "root", ROOT_PASS),
    ],
)
def test_despues_del_cambio_solo_la_nueva_permite_ingresar(client, request, fixture, usuario, actual):
    headers = request.getfixturevalue(fixture)
    assert _cambiar(client, headers, actual, "nueva-clave").status_code == 204
    assert _login(client, usuario, actual) == 401
    assert _login(client, usuario, "nueva-clave") == 200


def test_sin_restricciones_adicionales_de_formato(client, cliente_headers):
    # RF-62: el cliente pidió que el cambio no tenga restricciones adicionales.
    assert _cambiar(client, cliente_headers, "clave-segura", "1").status_code == 204
    assert _login(client, "analopez", "1") == 200


def test_requiere_sesion(client):
    assert (
        client.put(
            "/usuarios/me/contrasena", json={"actual": "a", "nueva": "b", "confirmacion": "b"}
        ).status_code
        == 401
    )
