import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app import bootstrap
from app.config import get_settings
from app.errores import ErrorNegocio, manejar_error_negocio, manejar_validacion
from app.routers import administradores, auth, carrito, monedero, noticias, reservas, usuarios, vuelos

logging.basicConfig(level=logging.INFO)


def _liberar_vencidas() -> None:
    from app.db import SessionLocal
    from app.services.reservas import liberar_vencidas

    with SessionLocal() as db:
        liberar_vencidas(db)
        db.commit()


async def _revisar_vencidas(cada: int) -> None:
    """Actor «Tiempo» (CU-32): revisa periódicamente las reservas sin pago que vencieron."""
    log = logging.getLogger("tareas")
    while True:
        await asyncio.sleep(cada)
        try:
            await asyncio.to_thread(_liberar_vencidas)
        except Exception:  # noqa: BLE001 — la revisión se reintenta en la siguiente vuelta
            log.exception("No se pudieron liberar las reservas vencidas")


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    try:
        bootstrap.main()
    except Exception:  # noqa: BLE001 — sin base de datos la API arranca y /salud lo indica
        logging.getLogger("bootstrap").exception("No se pudo preparar el usuario root")
    s = get_settings()
    tarea = (
        asyncio.create_task(_revisar_vencidas(s.revisar_vencidas_cada_seg)) if s.tareas_periodicas else None
    )
    yield
    if tarea:
        tarea.cancel()
        with suppress(asyncio.CancelledError):
            await tarea


def crear_app() -> FastAPI:
    app = FastAPI(
        title="API · Tiquetes aéreos",
        description="Sistema de gestión de compra y reserva de tiquetes aéreos en línea · Iteraciones 1 y 2",
        version="0.2.0",
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

    for r in (auth, usuarios, administradores, vuelos, noticias, reservas, carrito, monedero):
        app.include_router(r.router)

    @app.get("/salud", tags=["Sistema"])
    def salud():
        return {"estado": "ok"}

    return app


app = crear_app()
