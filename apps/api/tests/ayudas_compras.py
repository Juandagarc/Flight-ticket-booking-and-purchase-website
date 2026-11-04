"""Ayudas para las pruebas de la iteración 2."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text


def viajero(documento: str = "1088123456", **cambios) -> dict:
    datos = {
        "documento": documento,
        "nombres": "Ana María",
        "apellidos": "López Restrepo",
        "fecha_nacimiento": "1995-04-12",
        "genero": "FEMENINO",
        "telefono": "3001234567",
        "correo": f"{documento.lower()}@example.com",
        "nombre_contacto": "Carlos López",
        "telefono_contacto": "3109876543",
    }
    datos.update(cambios)
    return datos


def reserva(vuelo: str, *pasajeros: dict, clase: str = "ECONOMICA", regreso: str | None = None) -> dict:
    cuerpo = {"vuelo_codigo": vuelo, "clase": clase, "pasajeros": list(pasajeros) or [viajero()]}
    if regreso:
        cuerpo["vuelo_regreso_codigo"] = regreso
    return cuerpo


@pytest.fixture
def vuelo(programar):
    """Vuelo nacional Pereira–Bogotá en 10 días: primera 650 000, económica 280 000."""
    return programar()


@pytest.fixture
def reservar(client, cliente_headers):
    def _reservar(cuerpo: dict, headers: dict | None = None, esperado: int = 201) -> dict:
        r = client.post("/reservas", json=cuerpo, headers=headers or cliente_headers)
        assert r.status_code == esperado, r.text
        return r.json()

    return _reservar


@pytest.fixture
def con_saldo(client, cliente_headers):
    def _con_saldo(valor: str, headers: dict | None = None) -> dict:
        r = client.put("/monedero/saldo", json={"saldo": valor}, headers=headers or cliente_headers)
        assert r.status_code == 200, r.text
        return r.json()

    return _con_saldo


def mover_salida(db, codigo: str, horas: float) -> None:
    """Deja la salida del vuelo a `horas` del momento actual."""
    db.execute(
        text("UPDATE vuelo SET fecha_hora_salida = :s WHERE codigo = :c"),
        {"s": datetime.now(UTC) + timedelta(hours=horas), "c": codigo},
    )
    db.commit()
    db.expire_all()


def envejecer_reserva(db, codigo: str, horas: float = 25) -> None:
    """Simula el paso del tiempo: la reserva se creó hace `horas` horas."""
    db.execute(
        text("UPDATE reserva SET fecha_creacion = :creada, fecha_expiracion = :vence WHERE codigo = :c"),
        {
            "creada": datetime.now(UTC) - timedelta(hours=horas),
            "vence": datetime.now(UTC) - timedelta(hours=horas - 24),
            "c": codigo,
        },
    )
    db.commit()
    db.expire_all()
