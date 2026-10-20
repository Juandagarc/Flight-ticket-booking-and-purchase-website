import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app import bootstrap
from app.config import get_settings
from app.errores import ErrorNegocio, manejar_error_negocio, manejar_validacion
from app.routers import administradores, auth, noticias, reservas, usuarios, vuelos

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    try:
        bootstrap.main()
    except Exception:  # noqa: BLE001 — sin base de datos la API arranca y /salud lo indica
        logging.getLogger("bootstrap").exception("No se pudo preparar el usuario root")
    yield


def crear_app() -> FastAPI:
    app = FastAPI(
        title="API · Tiquetes aéreos",
        description="Sistema de gestión de compra y reserva de tiquetes aéreos en línea · Iteración 1",
        version="0.1.0",
        lifespan=ciclo_de_vida,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().lista_cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(ErrorNegocio, manejar_error_negocio)
    app.add_exception_handler(RequestValidationError, manejar_validacion)

    for r in (auth, usuarios, administradores, vuelos, noticias, reservas):
        app.include_router(r.router)

    @app.get("/salud", tags=["Sistema"])
    def salud():
        return {"estado": "ok"}

    return app


app = crear_app()
