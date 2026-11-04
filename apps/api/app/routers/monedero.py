"""HU-014 Gestión del monedero (CU-36). Monedero interno y simulado (RF-38, RF-70, RF-71)."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_cliente
from app.errores import ErrorNegocio
from app.models import MovimientoMonedero, Tarjeta, Usuario
from app.schemas import AjusteSaldo, MonederoSalida, TarjetaNueva, TarjetaSalida
from app.services.monedero import TipoMovimiento, monedero_de, mover_saldo

router = APIRouter(prefix="/monedero", tags=["Monedero"])


def _salida(db: Session, cliente: Usuario) -> MonederoSalida:
    m = monedero_de(db, cliente.id)
    return MonederoSalida(
        saldo=m.saldo,
        tarjetas=db.scalars(
            select(Tarjeta).where(Tarjeta.monedero_id == m.id).order_by(Tarjeta.franquicia)
        ).all(),
        movimientos=db.scalars(
            select(MovimientoMonedero)
            .where(MovimientoMonedero.monedero_id == m.id)
            .order_by(MovimientoMonedero.fecha.desc(), MovimientoMonedero.id)
            .limit(100)
        ).all(),
    )


@router.get("", response_model=MonederoSalida)
def ver_monedero(cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    salida = _salida(db, cliente)
    db.commit()
    return salida


@router.post("/tarjetas", response_model=TarjetaSalida, status_code=status.HTTP_201_CREATED)
def agregar_tarjeta(
    datos: TarjetaNueva, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)
):
    """Solo se guardan franquicia, titular, últimos cuatro dígitos y vencimiento; nunca el número."""
    m = monedero_de(db, cliente.id)
    tarjeta = Tarjeta(
        monedero_id=m.id,
        tipo=datos.tipo,
        franquicia=datos.franquicia,
        titular=datos.titular,
        ultimos_digitos=datos.numero[-4:],
        vencimiento=datos.vencimiento,
    )
    db.add(tarjeta)
    db.commit()
    return tarjeta


@router.delete("/tarjetas/{tarjeta_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_tarjeta(
    tarjeta_id: uuid.UUID, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)
):
    m = monedero_de(db, cliente.id)
    tarjeta = db.get(Tarjeta, tarjeta_id)
    if tarjeta is None or tarjeta.monedero_id != m.id:
        raise ErrorNegocio(404, "TARJETA_NO_ENCONTRADA", "La tarjeta no existe.")
    db.delete(tarjeta)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/saldo", response_model=MonederoSalida)
def ajustar_saldo(
    datos: AjusteSaldo, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)
):
    """RF-70: el cliente edita su saldo a mano; el ajuste queda registrado como movimiento."""
    m = monedero_de(db, cliente.id, bloquear=True)
    diferencia = datos.saldo - m.saldo
    if diferencia == 0:
        raise ErrorNegocio(422, "SALDO_IGUAL", "El nuevo saldo es igual al actual.", "saldo")
    mover_saldo(db, m, TipoMovimiento.AJUSTE_MANUAL, diferencia, "Ajuste manual del saldo")
    db.commit()
    return _salida(db, cliente)
