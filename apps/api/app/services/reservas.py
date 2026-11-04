"""Reglas de reserva, compra, carrito, pago y cancelación (HU-010 a HU-018).

Una compra es una reserva pagada (RF-55): las dos bloquean sillas. Una reserva sin pago se
sostiene 24 horas (RF-14) y luego vence. Al cancelar o vencer, los tiquetes pasan a CANCELADO,
lo que libera las sillas en los índices únicos parciales del modelo.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errores import ErrorNegocio
from app.models import (
    ActividadUsuario,
    Carrito,
    EstadoReserva,
    Pago,
    Pasajero,
    Perfil,
    Reembolso,
    Reserva,
    Tiquete,
    Usuario,
    Vuelo,
)
from app.services.correo import Correo, obtener_enviador
from app.services.monedero import TipoMovimiento, monedero_de, mover_saldo
from app.services.vuelos import salida_local

log = logging.getLogger("reservas")

MAX_TIQUETES_POR_VUELO = 5  # RF-15: reservas vigentes y compras del cliente en el vuelo
EDAD_ADULTO = 18
# RF-58: plazo para cancelar una compra antes de la salida.
PLAZO_CANCELACION = {"NACIONAL": timedelta(hours=1), "INTERNACIONAL": timedelta(hours=3)}
_ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I para que se lea sin confusión


def ahora() -> datetime:
    return datetime.now(UTC)


def llegada_utc(vuelo: Vuelo) -> datetime:
    return vuelo.fecha_hora_salida + timedelta(minutes=vuelo.duracion_min)


def edad_en(nacimiento: date, fecha: date) -> int:
    return fecha.year - nacimiento.year - ((fecha.month, fecha.day) < (nacimiento.month, nacimiento.day))


# --- Vencimiento (HU-018) -----------------------------------------------------------


def liberar_vencidas(db: Session, momento: datetime | None = None) -> list[str]:
    """Pasa a VENCIDA toda reserva sin pago cuyo plazo terminó y libera sus sillas."""
    momento = momento or ahora()
    codigos = list(
        db.scalars(
            update(Reserva)
            .where(Reserva.estado == EstadoReserva.RESERVADA, Reserva.fecha_expiracion <= momento)
            .values(estado=EstadoReserva.VENCIDA, carrito_id=None)
            .returning(Reserva.codigo)
        )
    )
    if codigos:
        db.execute(update(Tiquete).where(Tiquete.reserva_codigo.in_(codigos)).values(estado="CANCELADO"))
        db.expire_all()
        log.info("Reservas vencidas liberadas: %s", ", ".join(codigos))
    return codigos


# --- Creación de la reserva (HU-010, HU-011) -------------------------------------------


@dataclass
class DatosPasajero:
    documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    genero: str
    telefono: str
    correo: str
    nombre_contacto: str
    telefono_contacto: str


def _vuelo_vendible(db: Session, codigo: str, campo: str) -> Vuelo:
    vuelo = db.scalar(select(Vuelo).where(Vuelo.codigo == codigo.upper()).with_for_update(of=Vuelo))
    if vuelo is None:
        raise ErrorNegocio(404, "VUELO_NO_ENCONTRADO", "El vuelo no existe.", campo)
    if vuelo.estado != "PROGRAMADO" or vuelo.fecha_hora_salida <= ahora():
        raise ErrorNegocio(
            409, "VUELO_NO_DISPONIBLE", f"El vuelo {vuelo.codigo} ya no está a la venta.", campo
        )
    return vuelo


def _nuevo_codigo(db: Session) -> str:
    while True:
        codigo = "".join(secrets.choice(_ALFABETO) for _ in range(6))
        if db.get(Reserva, codigo) is None:
            return codigo


def _sillas_libres(db: Session, vuelo: Vuelo, clase: str, cuantas: int) -> list[int]:
    """RF-20 y RF-21: sillas al azar de la clase escogida que no estén reservadas ni compradas."""
    filas = db.execute(
        text(
            """
            SELECT s.numero FROM silla s
            WHERE s.tipo_vuelo = :tipo AND s.clase = :clase
              AND s.numero NOT IN (
                SELECT t.silla_numero FROM tiquete t
                WHERE t.vuelo_codigo = :vuelo AND t.estado <> 'CANCELADO')
            ORDER BY random() LIMIT :n
            """
        ),
        {"tipo": vuelo.tipo, "clase": clase, "vuelo": vuelo.codigo, "n": cuantas},
    ).scalars()
    sillas = list(filas)
    if len(sillas) < cuantas:
        nombre = "primera clase" if clase == "PRIMERA" else "clase económica"
        raise ErrorNegocio(
            409,
            "SIN_SILLAS",
            f"El vuelo {vuelo.codigo} no tiene {cuantas} sillas libres en {nombre}.",
            "clase",
        )
    return sillas


def _validar_tope_y_repetidos(db: Session, cliente: Usuario, vuelo: Vuelo, documentos: list[str]) -> None:
    vigentes = db.scalar(
        select(func.count())
        .select_from(Tiquete)
        .join(Reserva, Reserva.codigo == Tiquete.reserva_codigo)
        .where(
            Reserva.cliente_id == cliente.id,
            Reserva.estado.in_([EstadoReserva.RESERVADA, EstadoReserva.PAGADA]),
            Tiquete.vuelo_codigo == vuelo.codigo,
            Tiquete.estado != "CANCELADO",
        )
    )
    if vigentes + len(documentos) > MAX_TIQUETES_POR_VUELO:
        disponibles = MAX_TIQUETES_POR_VUELO - vigentes
        raise ErrorNegocio(
            409,
            "TOPE_TIQUETES",
            f"Cada cliente puede tener máximo {MAX_TIQUETES_POR_VUELO} tiquetes por vuelo. "
            f"En el vuelo {vuelo.codigo} ya tienes {vigentes}; puedes agregar {max(disponibles, 0)} más.",
            "pasajeros",
        )
    repetidos = db.scalars(
        select(Tiquete.pasajero_documento).where(
            Tiquete.vuelo_codigo == vuelo.codigo,
            Tiquete.estado != "CANCELADO",
            Tiquete.pasajero_documento.in_(documentos),
        )
    ).all()
    if repetidos:
        raise ErrorNegocio(
            409,
            "PASAJERO_REPETIDO",
            f"El viajero con documento {repetidos[0]} ya tiene tiquete en el vuelo {vuelo.codigo}.",
            "pasajeros",
        )


def _guardar_pasajero(db: Session, datos: DatosPasajero) -> Pasajero:
    pasajero = db.get(Pasajero, datos.documento)
    if pasajero is None:
        pasajero = Pasajero(documento=datos.documento)
        db.add(pasajero)
    for campo, valor in vars(datos).items():
        if campo != "documento":
            setattr(pasajero, campo, valor)
    if pasajero.cliente_id is None:
        # RF-41: si el viajero es un cliente registrado, se enlaza para autocompletar después.
        dueno = db.scalar(
            select(Usuario.id)
            .join(Perfil, Perfil.usuario_id == Usuario.id)
            .where(Perfil.documento == datos.documento, Usuario.rol == "CLIENTE")
        )
        if dueno and db.scalar(select(Pasajero).where(Pasajero.cliente_id == dueno)) is None:
            pasajero.cliente_id = dueno
    return pasajero


def crear_reserva(
    db: Session,
    cliente: Usuario,
    vuelo_codigo: str,
    clase: str,
    pasajeros: list[DatosPasajero],
    regreso_codigo: str | None = None,
) -> Reserva:
    documentos = [p.documento for p in pasajeros]
    if len(set(documentos)) != len(documentos):
        raise ErrorNegocio(
            422, "PASAJERO_REPETIDO", "Un mismo viajero aparece dos veces en la reserva.", "pasajeros"
        )

    vuelos = [_vuelo_vendible(db, vuelo_codigo, "vuelo_codigo")]
    if regreso_codigo:
        ida = vuelos[0]
        regreso = _vuelo_vendible(db, regreso_codigo, "vuelo_regreso_codigo")
        if (regreso.origen, regreso.destino) != (ida.destino, ida.origen):
            raise ErrorNegocio(
                422,
                "REGRESO_INVALIDO",
                "El vuelo de regreso debe ir del destino al origen del vuelo de ida.",
                "vuelo_regreso_codigo",
            )
        if regreso.fecha_hora_salida <= llegada_utc(ida):
            raise ErrorNegocio(
                422,
                "REGRESO_INVALIDO",
                "El vuelo de regreso debe salir después de la llegada del vuelo de ida.",
                "vuelo_regreso_codigo",
            )
        vuelos.append(regreso)

    # RF-25: ningún menor viaja solo; la edad se cuenta a la fecha del primer vuelo.
    fecha_viaje = salida_local(vuelos[0]).date()
    if not any(edad_en(p.fecha_nacimiento, fecha_viaje) >= EDAD_ADULTO for p in pasajeros):
        raise ErrorNegocio(
            422,
            "MENOR_SOLO",
            "Un menor de edad no puede viajar solo: incluye al menos un adulto en la reserva.",
            "pasajeros",
        )

    for vuelo in vuelos:
        _validar_tope_y_repetidos(db, cliente, vuelo, documentos)

    registros = [_guardar_pasajero(db, p) for p in pasajeros]
    db.flush()

    carrito = db.scalar(select(Carrito).where(Carrito.cliente_id == cliente.id))
    if carrito is None:
        carrito = Carrito(cliente_id=cliente.id)
        db.add(carrito)
        db.flush()

    momento = ahora()
    vence = min(momento + timedelta(hours=get_settings().horas_reserva), vuelos[0].fecha_hora_salida)
    reserva = Reserva(
        codigo=_nuevo_codigo(db),
        cliente_id=cliente.id,
        carrito_id=carrito.id,
        estado=EstadoReserva.RESERVADA,
        tipo_trayecto="IDA_Y_VUELTA" if len(vuelos) == 2 else "SENCILLO",
        fecha_creacion=momento,
        fecha_expiracion=vence,
    )
    total = Decimal("0")
    for vuelo in vuelos:
        precio = vuelo.tarifa(clase)
        for pasajero, silla in zip(registros, _sillas_libres(db, vuelo, clase, len(registros)), strict=True):
            reserva.tiquetes.append(
                Tiquete(
                    vuelo_codigo=vuelo.codigo,
                    tipo_vuelo=vuelo.tipo,
                    pasajero_documento=pasajero.documento,
                    silla_numero=silla,
                    clase=clase,
                    precio=precio,
                )
            )
            total += precio
        db.add(
            ActividadUsuario(cliente_id=cliente.id, tipo="RESERVA", vuelo_codigo=vuelo.codigo, fecha=momento)
        )
    reserva.total = total
    carrito.fecha_actualizacion = momento
    db.add(reserva)
    db.flush()
    return reserva


# --- Pago con monedero (HU-013) --------------------------------------------------------


def _reservas_del_cliente(db: Session, cliente: Usuario, codigos: list[str]) -> list[Reserva]:
    codigos = sorted({c.upper() for c in codigos})
    reservas = list(
        db.scalars(
            select(Reserva)
            .where(Reserva.codigo.in_(codigos), Reserva.cliente_id == cliente.id)
            .with_for_update(of=Reserva)
        )
    )
    encontrados = {r.codigo for r in reservas}
    faltan = [c for c in codigos if c not in encontrados]
    if faltan:
        raise ErrorNegocio(404, "RESERVA_NO_ENCONTRADA", f"No encontramos la reserva {faltan[0]}.")
    return reservas


def pagar(db: Session, cliente: Usuario, codigos: list[str]) -> Pago:
    """Paga en una sola transacción las reservas indicadas (RF-18, RF-57, RF-71, RF-72).

    Si el saldo no alcanza no se debita nada ni se registra la compra, y las sillas siguen
    reservadas hasta su vencimiento.
    """
    reservas = _reservas_del_cliente(db, cliente, codigos)
    momento = ahora()
    for r in reservas:
        if r.estado != EstadoReserva.RESERVADA:
            estado = {"PAGADA": "ya está pagada", "VENCIDA": "venció", "CANCELADA": "fue cancelada"}
            raise ErrorNegocio(
                409,
                "RESERVA_NO_PAGABLE",
                f"La reserva {r.codigo} {estado.get(r.estado, 'no se puede pagar')}.",
            )
        for t in r.tiquetes:
            if t.vuelo.estado != "PROGRAMADO" or t.vuelo.fecha_hora_salida <= momento:
                raise ErrorNegocio(
                    409, "VUELO_NO_DISPONIBLE", f"El vuelo {t.vuelo_codigo} ya no está a la venta."
                )

    total = sum((r.total for r in reservas), Decimal("0"))
    monedero = monedero_de(db, cliente.id, bloquear=True)
    referencia = ", ".join(r.codigo for r in reservas)
    movimiento = mover_saldo(
        db, monedero, TipoMovimiento.DEBITO_COMPRA, -total, f"Compra de tiquetes · reserva {referencia}"
    )
    pago = Pago(
        monedero_id=monedero.id,
        movimiento_id=movimiento.id,
        monto_total=total,
        estado="APROBADO",
        fecha=momento,
    )
    db.add(pago)
    db.flush()
    for r in reservas:
        r.estado = EstadoReserva.PAGADA
        r.pago_id = pago.id
        r.carrito_id = None
        for vuelo_codigo in sorted({t.vuelo_codigo for t in r.tiquetes}):
            db.add(
                ActividadUsuario(
                    cliente_id=cliente.id, tipo="COMPRA", vuelo_codigo=vuelo_codigo, fecha=momento
                )
            )
    db.flush()
    enviar_codigos(reservas)
    return pago


def enviar_codigos(reservas: list[Reserva]) -> None:
    """RF-19: el código de reserva llega por correo a cada viajero incluido."""
    enviador = obtener_enviador()
    for r in reservas:
        por_viajero: dict[str, list[Tiquete]] = {}
        for t in r.tiquetes:
            por_viajero.setdefault(t.pasajero.correo, []).append(t)
        for correo, tiquetes in por_viajero.items():
            p = tiquetes[0].pasajero
            lineas = [
                f"Vuelo {t.vuelo_codigo} {t.vuelo.ciudad_origen.nombre} – {t.vuelo.ciudad_destino.nombre}, "
                f"salida {salida_local(t.vuelo):%d/%m/%Y %H:%M} (hora local), silla {t.silla_numero} "
                f"({'primera clase' if t.clase == 'PRIMERA' else 'económica'})"
                for t in tiquetes
            ]
            try:
                enviador.enviar(
                    Correo(
                        para=correo,
                        asunto=f"Tu código de reserva {r.codigo}",
                        cuerpo=(
                            f"Hola {p.nombres},\n\nTu compra quedó confirmada. Código de reserva: {r.codigo}\n\n"
                            + "\n".join(lineas)
                            + "\n\nCon este código puedes hacer el check-in y el cambio de silla.\n"
                        ),
                    )
                )
            except Exception:  # noqa: BLE001 — un fallo de correo no deshace la compra
                log.exception("No se pudo enviar el código %s a %s", r.codigo, correo)


# --- Cancelaciones (HU-015, HU-016) ----------------------------------------------------


def limite_cancelacion(reserva: Reserva) -> datetime | None:
    """Último momento en que se puede cancelar una compra: el plazo del vuelo más próximo."""
    limites = [
        t.vuelo.fecha_hora_salida - PLAZO_CANCELACION[t.vuelo.tipo]
        for t in reserva.tiquetes
        if t.estado != "CANCELADO"
    ]
    return min(limites) if limites else None


def _liberar_sillas(reserva: Reserva) -> None:
    for t in reserva.tiquetes:
        t.estado = "CANCELADO"


def cancelar(db: Session, cliente: Usuario, codigo: str) -> Reserva:
    reserva = _reservas_del_cliente(db, cliente, [codigo])[0]
    momento = ahora()

    if reserva.estado == EstadoReserva.RESERVADA:
        if reserva.fecha_expiracion and reserva.fecha_expiracion <= momento:
            raise ErrorNegocio(409, "RESERVA_VENCIDA", "La reserva ya venció y sus sillas se liberaron.")
        reserva.estado = EstadoReserva.CANCELADA
        reserva.carrito_id = None
        _liberar_sillas(reserva)
        db.flush()
        return reserva

    if reserva.estado == EstadoReserva.PAGADA:
        limite = limite_cancelacion(reserva)
        if limite is None or momento > limite:
            raise ErrorNegocio(
                409,
                "FUERA_DE_PLAZO",
                "Ya no se puede cancelar: las compras se cancelan hasta una hora antes en vuelos "
                "nacionales y tres horas antes en internacionales.",
            )
        monedero = monedero_de(db, cliente.id, bloquear=True)
        movimiento = mover_saldo(
            db,
            monedero,
            TipoMovimiento.ABONO_REEMBOLSO,
            reserva.total,
            f"Reembolso del 100 % · reserva {reserva.codigo}",
        )
        db.add(
            Reembolso(
                reserva_codigo=reserva.codigo,
                movimiento_id=movimiento.id,
                monto=reserva.total,
                motivo="CANCELACION_CLIENTE",
                fecha=momento,
            )
        )
        reserva.estado = EstadoReserva.CANCELADA
        _liberar_sillas(reserva)
        db.flush()
        return reserva

    raise ErrorNegocio(409, "NO_CANCELABLE", "Esta reserva ya no se puede cancelar.")


# --- Carrito (HU-012) ------------------------------------------------------------------


def carrito_de(db: Session, cliente: Usuario) -> Carrito:
    carrito = db.scalar(select(Carrito).where(Carrito.cliente_id == cliente.id))
    if carrito is None:
        carrito = Carrito(cliente_id=cliente.id)
        db.add(carrito)
        db.flush()
    return carrito


def reservas_en_carrito(db: Session, cliente: Usuario) -> list[Reserva]:
    carrito = carrito_de(db, cliente)
    return list(
        db.scalars(
            select(Reserva)
            .where(Reserva.carrito_id == carrito.id, Reserva.estado == EstadoReserva.RESERVADA)
            .order_by(Reserva.fecha_creacion)
        )
    )


def poner_en_carrito(db: Session, cliente: Usuario, codigo: str, dentro: bool) -> Reserva:
    reserva = _reservas_del_cliente(db, cliente, [codigo])[0]
    if dentro and reserva.estado != EstadoReserva.RESERVADA:
        raise ErrorNegocio(409, "RESERVA_NO_PAGABLE", "Solo las reservas vigentes van al carrito.")
    carrito = carrito_de(db, cliente)
    reserva.carrito_id = carrito.id if dentro else None
    carrito.fecha_actualizacion = ahora()
    db.flush()
    return reserva
