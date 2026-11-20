"""Datos de prueba para la sustentación de las iteraciones 1 y 2.

Uso:
    uv run python -m app.datos_demo               # carga los datos si la base no los tiene
    uv run python -m app.datos_demo --reiniciar   # borra todo, migra de nuevo y carga

Los datos se crean con los mismos endpoints que usa la web, así que pasan por todas las
validaciones. Solo se toca la base directamente para simular el paso del tiempo (reserva vencida
y vuelo que sale en menos de una hora).
"""

import argparse
import logging
import sys
import warnings
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.bootstrap import asegurar_root
from app.config import get_settings
from app.db import SessionLocal
from app.main import crear_app
from app.models import Usuario, Vuelo
from app.services import vuelos as reglas
from app.services.correo import EnviadorMemoria, usar_enviador
from app.services.reservas import liberar_vencidas

ROOT_DEMO = "Root2026"
ADMIN = {"nombre_usuario": "admin", "contrasena": "Admin2026"}
CLAVE_CLIENTE = "Cliente2026"
BOGOTA = ZoneInfo("America/Bogota")

log = logging.getLogger("datos_demo")


def _perfil(documento, nombres, apellidos, nacimiento, genero, correo, ciudad="Pereira"):
    return {
        "documento": documento,
        "tipo_documento": "CEDULA",
        "nombres": nombres,
        "apellidos": apellidos,
        "fecha_nacimiento": nacimiento,
        "lugar_nacimiento": ciudad,
        "direccion_facturacion": f"Calle 19 # 8-34, {ciudad}",
        "genero": genero,
        "correo": correo,
    }


ANA = _perfil("1088245671", "Ana María", "López Restrepo", "1990-03-14", "FEMENINO", "ana.lopez@correo.com")
CARLOS = _perfil(
    "1094887123",
    "Carlos Andrés",
    "Ruiz Gómez",
    "1998-11-02",
    "MASCULINO",
    "carlos.ruiz@correo.com",
    "Armenia",
)


def _viajero(documento, nombres, apellidos, nacimiento, genero, correo):
    return {
        "documento": documento,
        "nombres": nombres,
        "apellidos": apellidos,
        "fecha_nacimiento": nacimiento,
        "genero": genero,
        "telefono": "3104567890",
        "correo": correo,
        "nombre_contacto": "Jorge López",
        "telefono_contacto": "3157654321",
    }


V_ANA = _viajero(
    ANA["documento"], ANA["nombres"], ANA["apellidos"], ANA["fecha_nacimiento"], "FEMENINO", ANA["correo"]
)
V_HIJO = _viajero("1088998877", "Samuel", "Gómez López", "2018-07-21", "MASCULINO", "ana.lopez@correo.com")
V_MAMA = _viajero(
    "24567890", "Rosa Elena", "Restrepo de López", "1958-01-30", "FEMENINO", "rosa.restrepo@correo.com"
)
V_ESPOSO = _viajero(
    "10123456", "Jorge Iván", "Gómez Arango", "1987-09-05", "MASCULINO", "jorge.gomez@correo.com"
)
V_AMIGA = _viajero(
    "1053778899", "Valentina", "Ospina Marín", "1993-05-18", "FEMENINO", "valentina.ospina@correo.com"
)

# (origen, destino, días desde hoy, hora local, primera, económica)
VUELOS = [
    ("PEI", "BOG", 3, "06:30", "620000", "250000"),
    ("BOG", "PEI", 6, "18:10", "620000", "250000"),
    ("PEI", "CTG", 8, "07:45", "780000", "320000"),
    ("CTG", "PEI", 12, "16:20", "780000", "320000"),
    ("BOG", "SMR", 5, "09:00", "720000", "300000"),
    ("SMR", "BOG", 9, "19:30", "720000", "300000"),
    ("MDE", "MIA", 15, "11:15", "3600000", "1600000"),
    ("PEI", "MAD", 20, "17:00", "3800000", "1900000"),
    ("BOG", "CLO", 4, "08:20", "590000", "260000"),
    ("PEI", "BAQ", 7, "10:05", "690000", "290000"),
    ("CLO", "ADZ", 10, "06:50", "850000", "380000"),
    ("BOG", "LON", 25, "21:15", "4200000", "2100000"),
    ("CTG", "NYC", 18, "14:00", "3900000", "1800000"),
    ("BOG", "BUE", 28, "23:30", "4100000", "2000000"),
    ("MDE", "BGA", 2, "15:30", "560000", "240000"),
    ("CLO", "PSO", 11, "07:10", "540000", "230000"),
]


class _Api:
    def __init__(self, client: TestClient):
        self.c = client

    def __call__(self, metodo: str, ruta: str, token: str | None = None, esperado: int = 200, **kw):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = self.c.request(metodo, ruta, headers=headers, **kw)
        if r.status_code != esperado:
            raise RuntimeError(f"{metodo} {ruta} → {r.status_code}: {r.text}")
        return r.json() if r.content else None

    def token(self, usuario: str, clave: str) -> str:
        return self("POST", "/auth/login", json={"nombre_usuario": usuario, "contrasena": clave})[
            "access_token"
        ]


def _fecha(dias: int) -> str:
    return (datetime.now(BOGOTA) + timedelta(days=dias)).date().isoformat()


def ya_cargados() -> bool:
    with SessionLocal() as db:
        return db.scalar(select(Usuario).where(Usuario.nombre_usuario == ADMIN["nombre_usuario"])) is not None


def reiniciar_base() -> None:
    from alembic.config import Config

    from alembic import command

    with SessionLocal() as db:
        db.execute(text("DROP SCHEMA public CASCADE"))
        db.execute(text("CREATE SCHEMA public"))
        db.commit()
    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    command.upgrade(cfg, "head")


def cargar() -> dict:
    ajustes = get_settings()
    clave_root = ajustes.root_password or ROOT_DEMO
    with SessionLocal() as db:
        asegurar_root(db, clave_root)

    usar_enviador(EnviadorMemoria())  # los correos de la carga no se envían
    api = _Api(TestClient(crear_app()))

    # Usuarios ---------------------------------------------------------------------------
    root = api.token("root", clave_root)
    api("POST", "/administradores", root, 201, json=ADMIN)
    admin = api.token(ADMIN["nombre_usuario"], ADMIN["contrasena"])
    api(
        "POST",
        "/usuarios/me/perfil",
        admin,
        201,
        json=_perfil(
            "1087654321", "Daniela", "Mejía Castaño", "1985-06-09", "FEMENINO", "daniela.mejia@flight.co"
        ),
    )
    api(
        "POST",
        "/auth/registro",
        None,
        201,
        json={**ANA, "nombre_usuario": "ana.lopez", "contrasena": CLAVE_CLIENTE},
    )
    api(
        "POST",
        "/auth/registro",
        None,
        201,
        json={**CARLOS, "nombre_usuario": "carlos.ruiz", "contrasena": CLAVE_CLIENTE},
    )
    ana = api.token("ana.lopez", CLAVE_CLIENTE)

    # Vuelos (quedan publicados en Noticias) ---------------------------------------------
    codigos: dict[tuple[str, str], str] = {}
    for origen, destino, dias, hora, primera, economica in VUELOS:
        v = api(
            "POST",
            "/vuelos",
            admin,
            201,
            json={
                "origen": origen,
                "destino": destino,
                "fecha_salida": _fecha(dias),
                "hora_salida": hora,
                "tarifa_primera": primera,
                "tarifa_economica": economica,
            },
        )
        codigos[(origen, destino)] = v["codigo"]
    # Vuelo que sale pronto: con él se muestra que una compra ya no se puede cancelar.
    pronto = api(
        "POST",
        "/vuelos",
        admin,
        201,
        json={
            "origen": "PEI",
            "destino": "MDE",
            "fecha_salida": _fecha(1),
            "hora_salida": "12:00",
            "tarifa_primera": "480000",
            "tarifa_economica": "210000",
        },
    )["codigo"]

    # Búsquedas de Ana (quedan en su actividad) -----------------------------------------
    for params in (
        {"origen": "PEI", "destino": "CTG"},
        {"origen": "PEI", "destino": "MAD"},
        {"destino": "SMR", "pasajeros": 2},
    ):
        api("GET", "/vuelos/buscar", ana, params=params)

    # Monedero de Ana ---------------------------------------------------------------------
    api("PUT", "/monedero/saldo", ana, json={"saldo": "10000000"})
    api(
        "POST",
        "/monedero/tarjetas",
        ana,
        201,
        json={
            "tipo": "CREDITO",
            "franquicia": "VISA",
            "titular": "ANA MARIA LOPEZ",
            "numero": "4111111111111111",
            "vencimiento": "09/29",
        },
    )
    api(
        "POST",
        "/monedero/tarjetas",
        ana,
        201,
        json={
            "tipo": "DEBITO",
            "franquicia": "MASTERCARD",
            "titular": "ANA MARIA LOPEZ",
            "numero": "5555555555554444",
            "vencimiento": "03/28",
        },
    )

    def reservar(ida, viajeros, clase="ECONOMICA", regreso=None):
        cuerpo = {"vuelo_codigo": codigos.get(ida, ida), "clase": clase, "pasajeros": viajeros}
        if regreso:
            cuerpo["vuelo_regreso_codigo"] = codigos[regreso]
        return api("POST", "/reservas", ana, 201, json=cuerpo)["codigo"]

    def pagar(*reservas):
        api("POST", "/pagos", ana, 201, json={"reservas": list(reservas)})

    def cancelar(codigo):
        api("POST", f"/reservas/{codigo}/cancelar", ana)

    # Reservas y compras de Ana -----------------------------------------------------------
    familia = reservar(("PEI", "CTG"), [V_ANA, V_HIJO, V_MAMA], regreso=("CTG", "PEI"))
    madrid = reservar(("PEI", "MAD"), [V_ANA, V_ESPOSO])
    pagar(familia, madrid)

    cancelada_compra = reservar(("BOG", "CLO"), [V_ANA])
    pagar(cancelada_compra)
    cancelar(cancelada_compra)

    cancelada_reserva = reservar(("PEI", "BOG"), [V_AMIGA])
    cancelar(cancelada_reserva)

    vencida = reservar(("PEI", "BAQ"), [V_ANA, V_ESPOSO])

    fuera_de_plazo = reservar(pronto, [V_ESPOSO])
    pagar(fuera_de_plazo)

    carrito = [reservar(("BOG", "SMR"), [V_AMIGA]), reservar(("MDE", "MIA"), [V_ANA, V_ESPOSO])]

    # Paso del tiempo simulado -------------------------------------------------------------
    with SessionLocal() as db:
        hace = datetime.now(UTC) - timedelta(hours=26)
        db.execute(
            text("UPDATE reserva SET fecha_creacion = :c, fecha_expiracion = :v WHERE codigo = :r"),
            {"c": hace, "v": hace + timedelta(hours=24), "r": vencida},
        )
        liberar_vencidas(db)
        vuelo = db.get(Vuelo, pronto)
        vuelo.fecha_hora_salida = datetime.now(UTC) + timedelta(minutes=50)
        vuelo.llegada_local = reglas.llegada_local(
            vuelo.fecha_hora_salida, vuelo.duracion_min, vuelo.ciudad_destino
        )
        db.commit()

    return {
        "root": clave_root,
        "reservas": {
            "pagada ida y vuelta (con un menor)": familia,
            "pagada internacional": madrid,
            "compra cancelada con reembolso": cancelada_compra,
            "reserva cancelada": cancelada_reserva,
            "reserva vencida": vencida,
            "compra fuera de plazo de cancelación": fuera_de_plazo,
            "en el carrito": ", ".join(carrito),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga los datos de prueba de la sustentación.")
    parser.add_argument("--reiniciar", action="store_true", help="borra toda la base y la vuelve a crear")
    args = parser.parse_args()
    if args.reiniciar:
        reiniciar_base()
    elif ya_cargados():
        print("Los datos de prueba ya están cargados. Usa --reiniciar para empezar de cero.")
        return
    try:
        resumen = cargar()
    except Exception as e:
        sys.exit(f"No se pudieron cargar los datos: {e}\nVuelve a intentarlo con --reiniciar.")
    print("\nDatos de prueba cargados.\n")
    print("Usuarios")
    print(f"  root          root          / {resumen['root']}")
    print(f"  administrador {ADMIN['nombre_usuario']:<13} / {ADMIN['contrasena']}")
    print(f"  cliente       ana.lopez     / {CLAVE_CLIENTE}   (con compras, reservas y saldo)")
    print(f"  cliente       carlos.ruiz   / {CLAVE_CLIENTE}   (cuenta nueva, sin saldo)")
    print("\nReservas de ana.lopez")
    for k, v in resumen["reservas"].items():
        print(f"  {v:<15} {k}")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    main()
