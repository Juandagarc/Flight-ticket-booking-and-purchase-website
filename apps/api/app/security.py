from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings


def cifrar_contrasena(contrasena: str) -> str:
    # bcrypt solo usa los primeros 72 bytes; se truncan de forma explícita.
    return bcrypt.hashpw(contrasena.encode()[:72], bcrypt.gensalt()).decode()


def verificar_contrasena(contrasena: str, contrasena_hash: str) -> bool:
    try:
        return bcrypt.checkpw(contrasena.encode()[:72], contrasena_hash.encode())
    except ValueError:
        # Hash inválido (p. ej. el marcador del script antes de definir la del root).
        return False


def crear_token(usuario_id: str, rol: str, nombre_usuario: str) -> str:
    s = get_settings()
    ahora = datetime.now(UTC)
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "usuario": nombre_usuario,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=s.jwt_minutos),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algoritmo)


def decodificar_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algoritmo])
