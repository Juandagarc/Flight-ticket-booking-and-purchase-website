"""Define la contraseña del root creado por defecto (RF-31).

El script del modelo crea el root con un marcador en lugar de contraseña. Al arrancar la API
(o con `python -m app.bootstrap`), si el root aún tiene el marcador y ROOT_PASSWORD está
definida, se guarda su hash. Si el root ya cambió su contraseña, no se toca.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import Rol, Usuario
from app.security import cifrar_contrasena

MARCADOR = "CAMBIAR_AL_DESPLEGAR"
log = logging.getLogger("bootstrap")


def asegurar_root(db: Session, contrasena: str | None) -> bool:
    root = db.scalar(select(Usuario).where(Usuario.rol == Rol.ROOT))
    if root is None or root.contrasena_hash != MARCADOR:
        return False
    if not contrasena:
        log.warning("El root no tiene contraseña: define ROOT_PASSWORD para poder ingresar.")
        return False
    root.contrasena_hash = cifrar_contrasena(contrasena)
    db.commit()
    log.info("Contraseña inicial del root definida.")
    return True


def main() -> None:
    with SessionLocal() as db:
        asegurar_root(db, get_settings().root_password)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
