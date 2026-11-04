"""HU-010 Reserva, HU-011 Compra, HU-013 Pago, HU-015 y HU-016 Cancelaciones, HU-017 Histórico.

Solo un cliente reserva o compra (RF-33, RF-34): el visitante debe registrarse o iniciar sesión,
y un root o administrador nunca puede hacerlo.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_cliente, reservas_al_dia
from app.models import EstadoReserva, Reembolso, Reserva, Silla, Usuario
from app.schemas import (
    CiudadCorta,
    PagoNuevo,
    PagoSalida,
    ReservaDetalle,
    ReservaNueva,
    ReservaResumen,
    TiqueteSalida,
    TramoSalida,
)
from app.services import reservas as servicio
from app.services.monedero import monedero_de
from app.services.vuelos import salida_local

router = APIRouter(tags=["Reserva y compra"], dependencies=[Depends(reservas_al_dia)])


def resumen(reserva: Reserva) -> ReservaResumen:
    """Datos de una reserva para listas y carrito: tramos, viajeros, total y acciones posibles."""
    ahora = datetime.now(UTC)
    tramos: dict[str, TramoSalida] = {}
    viajeros: set[str] = set()
    for t in reserva.tiquetes:
        viajeros.add(t.pasajero_documento)
        tramo = tramos.get(t.vuelo_codigo)
        if tramo is None:
            v = t.vuelo
            tramo = tramos[t.vuelo_codigo] = TramoSalida(
                vuelo_codigo=v.codigo,
                tipo_vuelo=v.tipo,
                origen=CiudadCorta.model_validate(v.ciudad_origen),
                destino=CiudadCorta.model_validate(v.ciudad_destino),
                salida_local=salida_local(v),
                llegada_local=v.llegada_local,
                duracion_min=v.duracion_min,
                clase=t.clase,
                viajeros=0,
                precio_unitario=t.precio,
                subtotal=0,
            )
        tramo.viajeros += 1
        tramo.subtotal += t.precio
    ordenados = sorted(tramos.values(), key=lambda x: x.salida_local)
    vigente = reserva.estado == EstadoReserva.RESERVADA and (
        reserva.fecha_expiracion is None or reserva.fecha_expiracion > ahora
    )
    limite = servicio.limite_cancelacion(reserva) if reserva.estado == EstadoReserva.PAGADA else None
    return ReservaResumen(
        codigo=reserva.codigo,
        estado=reserva.estado,
        tipo_trayecto=reserva.tipo_trayecto,
        clase=reserva.tiquetes[0].clase if reserva.tiquetes else "",
        tramos=ordenados,
        viajeros=len(viajeros),
        total=reserva.total,
        fecha_creacion=reserva.fecha_creacion,
        fecha_expiracion=reserva.fecha_expiracion if reserva.estado == EstadoReserva.RESERVADA else None,
        en_carrito=reserva.carrito_id is not None and vigente,
        puede_pagar=vigente,
        puede_cancelar=vigente or (limite is not None and ahora <= limite),
        limite_cancelacion=limite,
    )


def detalle(db: Session, reserva: Reserva) -> ReservaDetalle:
    base = resumen(reserva)
    sillas = {
        (s.tipo_vuelo, s.numero): s
        for s in db.scalars(
            select(Silla).where(Silla.numero.in_([t.silla_numero for t in reserva.tiquetes] or [0]))
        )
    }
    tiquetes = []
    for t in sorted(reserva.tiquetes, key=lambda x: (x.vuelo.fecha_hora_salida, x.pasajero.apellidos)):
        s = sillas[(t.tipo_vuelo, t.silla_numero)]
        tiquetes.append(
            TiqueteSalida(
                id=t.id,
                vuelo_codigo=t.vuelo_codigo,
                origen=CiudadCorta.model_validate(t.vuelo.ciudad_origen),
                destino=CiudadCorta.model_validate(t.vuelo.ciudad_destino),
                tipo_vuelo=t.tipo_vuelo,
                salida_local=salida_local(t.vuelo),
                llegada_local=t.vuelo.llegada_local,
                pasajero_documento=t.pasajero_documento,
                pasajero_nombre=f"{t.pasajero.nombres} {t.pasajero.apellidos}",
                silla=t.silla_numero,
                fila=s.fila,
                columna=s.columna,
                posicion=s.posicion,
                clase=t.clase,
                precio=t.precio,
                estado=t.estado,
                checkin="REALIZADO" if t.estado == "CON_CHECKIN" else "PENDIENTE",
            )
        )
    reembolso = db.scalar(select(Reembolso).where(Reembolso.reserva_codigo == reserva.codigo))
    return ReservaDetalle(
        **base.model_dump(),
        tiquetes=tiquetes,
        pago_fecha=reserva.pago.fecha if reserva.pago else None,
        reembolso=reembolso.monto if reembolso else None,
        reembolso_fecha=reembolso.fecha if reembolso else None,
    )


def _datos(p) -> servicio.DatosPasajero:
    return servicio.DatosPasajero(**p.model_dump(exclude={"correo"}), correo=str(p.correo))


@router.get("/reservas/acceso")
def acceso_a_reservar(usuario: Usuario = Depends(requiere_cliente)):
    return {"permitido": True, "usuario": usuario.nombre_usuario}


@router.post("/reservas", response_model=ReservaDetalle, status_code=status.HTTP_201_CREATED)
def reservar(
    datos: ReservaNueva,
    cliente: Usuario = Depends(requiere_cliente),
    db: Session = Depends(get_db),
):
    """Crea la reserva sin pago, bloquea las sillas y la deja en el carrito (RF-14, RF-55)."""
    reserva = servicio.crear_reserva(
        db,
        cliente,
        datos.vuelo_codigo,
        datos.clase,
        [_datos(p) for p in datos.pasajeros],
        regreso_codigo=datos.vuelo_regreso_codigo,
    )
    db.commit()
    db.refresh(reserva)
    return detalle(db, reserva)


@router.get("/reservas", response_model=list[ReservaResumen])
def historico(cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    """HU-017: reservas y compras del cliente en todos sus estados, la más reciente primero."""
    reservas = db.scalars(
        select(Reserva).where(Reserva.cliente_id == cliente.id).order_by(Reserva.fecha_creacion.desc())
    ).all()
    return [resumen(r) for r in reservas]


@router.get("/reservas/{codigo}", response_model=ReservaDetalle)
def ver_reserva(codigo: str, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    return detalle(db, servicio._reservas_del_cliente(db, cliente, [codigo])[0])


@router.post("/reservas/{codigo}/cancelar", response_model=ReservaDetalle)
def cancelar(codigo: str, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    """Cancela una reserva vigente (HU-016) o una compra dentro del plazo con reembolso (HU-015)."""
    reserva = servicio.cancelar(db, cliente, codigo)
    db.commit()
    db.refresh(reserva)
    return detalle(db, reserva)


@router.post("/pagos", response_model=PagoSalida, status_code=status.HTTP_201_CREATED)
def pagar(datos: PagoNuevo, cliente: Usuario = Depends(requiere_cliente), db: Session = Depends(get_db)):
    """HU-011 y HU-013: paga con el monedero, en una sola transacción, las reservas indicadas."""
    pago = servicio.pagar(db, cliente, datos.reservas)
    db.commit()
    return PagoSalida(
        id=pago.id,
        monto_total=pago.monto_total,
        fecha=pago.fecha,
        reservas=sorted(c.upper() for c in datos.reservas),
        saldo=monedero_de(db, cliente.id).saldo,
    )
