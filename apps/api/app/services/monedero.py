"""Monedero interno y simulado del cliente (RF-30, RF-38, RF-70 a RF-72).

Todo cambio de saldo pasa por `mover_saldo`, que bloquea la fila del monedero y deja un
movimiento con el saldo resultante. El saldo nunca queda negativo (decisión del equipo).
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errores import ErrorNegocio
from app.models import Monedero, MovimientoMonedero


class TipoMovimiento:
    AJUSTE_MANUAL = "AJUSTE_MANUAL"
    DEBITO_COMPRA = "DEBITO_COMPRA"
    ABONO_REEMBOLSO = "ABONO_REEMBOLSO"


def monedero_de(db: Session, cliente_id: uuid.UUID, bloquear: bool = False) -> Monedero:
    consulta = select(Monedero).where(Monedero.cliente_id == cliente_id)
    if bloquear:
        consulta = consulta.with_for_update()
    monedero = db.scalar(consulta)
    if monedero is None:
        # Todo cliente recibe su monedero al registrarse (RF-30); esto cubre cuentas antiguas.
        monedero = Monedero(cliente_id=cliente_id, saldo=Decimal("0"))
        db.add(monedero)
        db.flush()
    return monedero


def mover_saldo(
    db: Session, monedero: Monedero, tipo: str, monto: Decimal, descripcion: str
) -> MovimientoMonedero:
    """Suma `monto` (negativo para débitos) al saldo y registra el movimiento."""
    nuevo = (monedero.saldo + monto).quantize(Decimal("0.01"))
    if nuevo < 0:
        raise ErrorNegocio(
            402,
            "SALDO_INSUFICIENTE",
            f"Saldo insuficiente: tienes ${monedero.saldo:,.0f} y se necesitan ${-monto:,.0f}.",
        )
    monedero.saldo = nuevo
    movimiento = MovimientoMonedero(
        monedero_id=monedero.id,
        tipo=tipo,
        monto=monto,
        saldo_resultante=nuevo,
        descripcion=descripcion[:200],
    )
    db.add(movimiento)
    db.flush()
    return movimiento
