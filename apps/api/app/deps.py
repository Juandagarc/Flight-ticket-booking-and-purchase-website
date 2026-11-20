"""Dependencias de autenticación y control de acceso por rol (RNF-05)."""

import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorNegocio
from app.models import Rol, Usuario
from app.security import decodificar_token

_bearer = HTTPBearer(auto_error=False)


def usuario_opcional(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Usuario autenticado o None para un visitante. Un token inválido se trata como error."""
    if cred is None:
        return None
    try:
        datos = decodificar_token(cred.credentials)
        usuario_id = uuid.UUID(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise ErrorNegocio(401, "SESION_INVALIDA", "Tu sesión expiró. Inicia sesión de nuevo.") from None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise ErrorNegocio(401, "SESION_INVALIDA", "Tu sesión expiró. Inicia sesión de nuevo.")
    return usuario


def usuario_actual(usuario: Usuario | None = Depends(usuario_opcional)) -> Usuario:
    if usuario is None:
        raise ErrorNegocio(401, "NO_AUTENTICADO", "Debes iniciar sesión.")
    return usuario


def requiere_rol(*roles: str) -> Callable[..., Usuario]:
    def _dep(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise ErrorNegocio(403, "ROL_NO_PERMITIDO", "Tu rol no tiene acceso a esta opción.")
        return usuario

    return _dep


requiere_cliente = requiere_rol(Rol.CLIENTE)
requiere_administrador = requiere_rol(Rol.ADMINISTRADOR)
requiere_root = requiere_rol(Rol.ROOT)


def reservas_al_dia(db: Session = Depends(get_db)) -> None:
    """Libera las reservas vencidas antes de atender la solicitud (HU-018).

    La tarea periódica de la API ya lo hace cada minuto; esto garantiza que ninguna consulta
    vea como ocupada una silla de una reserva que venció entre dos revisiones.
    """
    from app.services.reservas import liberar_vencidas

    if liberar_vencidas(db):
        db.commit()
