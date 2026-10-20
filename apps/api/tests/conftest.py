"""Pruebas contra un PostgreSQL real.

Se crea una base de pruebas desde cero con las migraciones y cada prueba corre dentro de una
transacción que se revierte al terminar, así las pruebas no se afectan entre sí.

TEST_DATABASE_URL apunta al servidor (por defecto postgres@localhost:5432); la base
`tiquetes_test` se recrea en cada corrida.
"""

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

URL_BASE = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/tiquetes_test"
)
os.environ["DATABASE_URL"] = URL_BASE
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-con-longitud-suficiente-32b")

from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Rol, Usuario  # noqa: E402
from app.security import cifrar_contrasena  # noqa: E402
from app.services import correo  # noqa: E402

ROOT_PASS = "root-pruebas"
ADMIN_PASS = "admin-pruebas"


@pytest.fixture(scope="session")
def engine():
    url = make_url(URL_BASE)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        c.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()

    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    cfg.attributes["database_url"] = URL_BASE
    command.upgrade(cfg, "head")

    eng = create_engine(URL_BASE)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    conexion = engine.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def buzon():
    enviador = correo.EnviadorMemoria()
    correo.usar_enviador(enviador)
    yield enviador
    correo.usar_enviador(None)


@pytest.fixture
def client(db, buzon):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Ayudas --------------------------------------------------------------------------


def datos_cliente(**cambios) -> dict:
    datos = {
        "documento": "1088123456",
        "tipo_documento": "CEDULA",
        "nombres": "Ana María",
        "apellidos": "López Restrepo",
        "fecha_nacimiento": "1995-04-12",
        "lugar_nacimiento": "Pereira",
        "direccion_facturacion": "Calle 20 # 8-15, Pereira",
        "genero": "FEMENINO",
        "correo": "ana@example.com",
        "nombre_usuario": "analopez",
        "contrasena": "clave-segura",
    }
    datos.update(cambios)
    return datos


def login(client, usuario: str, contrasena: str) -> dict:
    r = client.post("/auth/login", json={"nombre_usuario": usuario, "contrasena": contrasena})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def registrar(client):
    def _registrar(**cambios) -> dict:
        datos = datos_cliente(**cambios)
        r = client.post("/auth/registro", json=datos)
        assert r.status_code == 201, r.text
        return login(client, datos["nombre_usuario"], datos["contrasena"])

    return _registrar


@pytest.fixture
def cliente_headers(registrar):
    return registrar()


@pytest.fixture
def root_headers(client, db):
    root = db.query(Usuario).filter_by(rol=Rol.ROOT).one()
    root.contrasena_hash = cifrar_contrasena(ROOT_PASS)
    db.commit()
    return login(client, "root", ROOT_PASS)


@pytest.fixture
def admin_headers(client, db):
    db.add(
        Usuario(nombre_usuario="admin1", contrasena_hash=cifrar_contrasena(ADMIN_PASS), rol=Rol.ADMINISTRADOR)
    )
    db.commit()
    return login(client, "admin1", ADMIN_PASS)


def manana(dias: int = 1) -> str:
    return (datetime.now(UTC) + timedelta(days=dias)).date().isoformat()


def datos_vuelo(**cambios) -> dict:
    datos = {
        "origen": "PEI",
        "destino": "BOG",
        "fecha_salida": manana(10),
        "hora_salida": "08:30",
        "tarifa_primera": "650000",
        "tarifa_economica": "280000",
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def programar(client, admin_headers):
    def _programar(**cambios) -> dict:
        r = client.post("/vuelos", json=datos_vuelo(**cambios), headers=admin_headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _programar
