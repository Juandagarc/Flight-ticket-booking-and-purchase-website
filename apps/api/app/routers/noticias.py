"""HU-009 Consulta de noticias y promociones (CU-14). Público, sin iniciar sesión (RF-64)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Noticia, Vuelo
from app.schemas import CiudadCorta, NoticiaSalida
from app.services.vuelos import salida_local

router = APIRouter(prefix="/noticias", tags=["Noticias"])


@router.get("", response_model=list[NoticiaSalida])
def listar_noticias(tipo: str | None = None, limite: int = 50, db: Session = Depends(get_db)):
    """Catálogo de noticias: cada vuelo programado y cada promoción vigente, el más reciente primero."""
    consulta = (
        select(Noticia)
        .join(Vuelo, Vuelo.codigo == Noticia.vuelo_codigo)
        .where(
            Noticia.vigente.is_(True),
            Vuelo.estado == "PROGRAMADO",
            Vuelo.fecha_hora_salida > datetime.now(UTC),
        )
        .order_by(Noticia.fecha_publicacion.desc())
        .limit(min(max(limite, 1), 100))
    )
    if tipo:
        consulta = consulta.where(Noticia.tipo == tipo.upper())
    return [
        NoticiaSalida(
            id=n.id,
            tipo=n.tipo,
            titulo=n.titulo,
            imagen_url=n.imagen_url,
            precio_unitario=n.precio_unitario,
            fecha_publicacion=n.fecha_publicacion,
            vuelo_codigo=n.vuelo_codigo,
            origen=CiudadCorta.model_validate(n.vuelo.ciudad_origen),
            destino=CiudadCorta.model_validate(n.vuelo.ciudad_destino),
            salida_local=salida_local(n.vuelo),
            llegada_local=n.vuelo.llegada_local,
        )
        for n in db.scalars(consulta).unique()
    ]
