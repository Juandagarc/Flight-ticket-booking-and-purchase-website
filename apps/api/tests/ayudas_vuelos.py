"""Datos de apoyo que la iteración 1 todavía no crea por la API (tiquetes, promociones, suscripciones)."""

import random
import string
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session


def id_de(db: Session, nombre_usuario: str) -> uuid.UUID:
    return db.execute(
        text("SELECT id FROM usuario WHERE nombre_usuario = :u"), {"u": nombre_usuario}
    ).scalar_one()


def vender_tiquete(
    db: Session,
    vuelo: dict,
    cliente: str = "analopez",
    estado: str = "RESERVADA",
    silla: int = 30,
    clase: str = "ECONOMICA",
) -> str:
    """Crea una reserva con un tiquete para el vuelo (como lo hará la iteración 2)."""
    codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    documento = f"P{random.randint(10**6, 10**7)}"
    db.execute(
        text(
            "INSERT INTO pasajero (documento, nombres, apellidos, fecha_nacimiento, genero, telefono, correo,"
            " nombre_contacto, telefono_contacto) VALUES (:d, 'Luis', 'Pérez', '1980-01-01', 'MASCULINO',"
            " '3000000000', 'luis@example.com', 'Marta', '3100000000')"
        ),
        {"d": documento},
    )
    db.execute(
        text(
            "INSERT INTO reserva (codigo, cliente_id, estado, tipo_trayecto, fecha_expiracion)"
            " VALUES (:c, :cli, :e, 'SENCILLO', :exp)"
        ),
        {"c": codigo, "cli": id_de(db, cliente), "e": estado, "exp": datetime.now(UTC) + timedelta(hours=24)},
    )
    db.execute(
        text(
            "INSERT INTO tiquete (reserva_codigo, vuelo_codigo, tipo_vuelo, pasajero_documento, silla_numero, clase, precio)"
            " VALUES (:r, :v, :t, :d, :s, :cl, 1)"
        ),
        {"r": codigo, "v": vuelo["codigo"], "t": vuelo["tipo"], "d": documento, "s": silla, "cl": clase},
    )
    db.commit()
    return codigo


def publicar_promocion(db: Session, vuelo: dict, precio: int = 199000) -> None:
    promo_id = db.execute(
        text(
            "INSERT INTO promocion (vuelo_codigo, tipo_descuento, valor, fecha_inicio, fecha_fin)"
            " VALUES (:v, 'VALOR_FIJO', 81000, now(), now() + interval '5 days') RETURNING id"
        ),
        {"v": vuelo["codigo"]},
    ).scalar_one()
    db.execute(
        text(
            "INSERT INTO noticia (vuelo_codigo, promocion_id, tipo, titulo, imagen_url, precio_unitario)"
            " VALUES (:v, :p, 'PROMOCION', 'Promoción relámpago', '/destinos/BOG.svg', :precio)"
        ),
        {"v": vuelo["codigo"], "p": promo_id, "precio": precio},
    )
    db.commit()


def suscribir(db: Session, cliente: str = "analopez") -> None:
    db.execute(text("INSERT INTO suscripcion (cliente_id) VALUES (:c)"), {"c": id_de(db, cliente)})
    db.commit()
