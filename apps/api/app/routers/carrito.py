"""HU-012 Carrito multivuelo (CU-25). Gestionar el carrito no toca el saldo del monedero."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_cliente, reservas_al_dia
from app.models import Usuario
from app.routers.reservas import resumen
from app.schemas import CarritoSalida
from app.services import reservas as servicio
from app.services.monedero import monedero_de

router = APIRouter(prefix="/carrito", tags=["Carrito"], dependencies=[Depends(reservas_al_dia)])


def _carrito(db: Session, cliente: Usuario) -> CarritoSalida:
    reservas = [resumen(r) for r in servicio.reservas_en_carrito(db, cliente)]
    return CarritoSalida(
        reservas=reservas,
        total=sum((r.total for r in reservas), Decimal("0")),
        saldo=monedero_de(db, cliente.id).saldo,
    )


@router.get("", response_model=CarritoSalida)
def ver_carrito(cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    carrito = _carrito(db, cliente)
    db.commit()
    return carrito


@router.delete("/{codigo}", response_model=CarritoSalida)
def retirar(codigo: str, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    """Saca la reserva del carrito. La reserva sigue vigente hasta su vencimiento (agregación)."""
    servicio.poner_en_carrito(db, cliente, codigo, dentro=False)
    db.commit()
    return _carrito(db, cliente)


@router.post("/{codigo}", response_model=CarritoSalida)
def volver_a_agregar(
    codigo: str, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)
):
    servicio.poner_en_carrito(db, cliente, codigo, dentro=True)
    db.commit()
    return _carrito(db, cliente)
