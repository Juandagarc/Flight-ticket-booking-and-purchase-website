"""Configuración de la API, leída de variables de entorno (o de un archivo .env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/tiquetes"

    jwt_secret: str = "cambiar-en-produccion"
    jwt_algoritmo: str = "HS256"
    jwt_minutos: int = 8 * 60

    # Contraseña inicial del usuario root (RF-31). Se aplica al arrancar si el root
    # todavía tiene la contraseña de marcador que deja el script del modelo.
    root_password: str | None = None

    # Dos letras de la aerolínea en el código de vuelo (RF-54, decisión del equipo: FL).
    aerolinea_codigo: str = "FL"
    # Velocidad promedio para calcular el tiempo de vuelo (RF-53: distancia / velocidad).
    velocidad_promedio_kmh: float = 800.0

    cors_origenes: str = "http://localhost:3000"

    # Correo (RNF-03). Sin SMTP_HOST los correos se escriben en el log.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_usuario: str | None = None
    smtp_contrasena: str | None = None
    smtp_remitente: str = "no-responder@flight.local"
    smtp_tls: bool = True

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origenes.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
