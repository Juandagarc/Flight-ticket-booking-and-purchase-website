"""CU-16 y CU-17: publicar el vuelo en Noticias y avisar a los suscriptores (RF-10, RF-66, RF-67)."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Noticia, Notificacion, Perfil, Suscripcion, Vuelo
from app.services.correo import Correo, obtener_enviador
from app.services.vuelos import precio_noticia, salida_local

log = logging.getLogger("notificaciones")


def titulo_vuelo(vuelo: Vuelo) -> str:
    return f"Nuevo vuelo {vuelo.ciudad_origen.nombre} – {vuelo.ciudad_destino.nombre}"


def publicar_vuelo(db: Session, vuelo: Vuelo) -> Noticia:
    noticia = Noticia(
        vuelo_codigo=vuelo.codigo,
        tipo="NUEVO_VUELO",
        titulo=titulo_vuelo(vuelo),
        imagen_url=vuelo.imagen_url,
        precio_unitario=precio_noticia(vuelo.tarifa("PRIMERA"), vuelo.tarifa("ECONOMICA")),
        fecha_publicacion=datetime.now(UTC),
    )
    db.add(noticia)
    db.flush()
    return noticia


def actualizar_noticias_del_vuelo(db: Session, vuelo: Vuelo) -> None:
    """Tras editar un vuelo, la noticia de su creación refleja la ruta, la imagen y el precio."""
    for noticia in db.scalars(
        select(Noticia).where(Noticia.vuelo_codigo == vuelo.codigo, Noticia.tipo == "NUEVO_VUELO")
    ):
        noticia.titulo = titulo_vuelo(vuelo)
        noticia.imagen_url = vuelo.imagen_url
        noticia.precio_unitario = precio_noticia(vuelo.tarifa("PRIMERA"), vuelo.tarifa("ECONOMICA"))


def avisar_suscriptores(db: Session, vuelo: Vuelo, noticia: Noticia) -> int:
    """Crea la notificación en la aplicación y envía el correo a cada suscripción activa.

    El envío se dispara con la creación del vuelo, no por horario (RF-67). Si un correo falla,
    queda registrado como no enviado y el vuelo se programa igual.
    """
    filas = db.execute(
        select(Suscripcion, Perfil)
        .join(Perfil, Perfil.usuario_id == Suscripcion.cliente_id)
        .where(Suscripcion.activa.is_(True))
    ).all()
    enviador = obtener_enviador()
    ahora = datetime.now(UTC)
    salida = salida_local(vuelo).strftime("%d/%m/%Y %H:%M")
    for suscripcion, perfil in filas:
        db.add(
            Notificacion(
                suscripcion_id=suscripcion.id,
                noticia_id=noticia.id,
                canal="APLICACION",
                enviada=True,
                fecha_envio=ahora,
            )
        )
        correo = Notificacion(suscripcion_id=suscripcion.id, noticia_id=noticia.id, canal="CORREO")
        try:
            enviador.enviar(
                Correo(
                    para=perfil.correo,
                    asunto=noticia.titulo,
                    cuerpo=(
                        f"Hola {perfil.nombres},\n\n"
                        f"Programamos el vuelo {vuelo.codigo} de {vuelo.ciudad_origen.nombre} a "
                        f"{vuelo.ciudad_destino.nombre}, con salida el {salida} (hora local), "
                        f"desde ${noticia.precio_unitario:,.0f} por persona.\n"
                    ),
                )
            )
            correo.enviada = True
            correo.fecha_envio = ahora
        except Exception:  # noqa: BLE001 — un fallo de correo no detiene la programación
            log.exception("No se pudo enviar el aviso a %s", perfil.correo)
        db.add(correo)
    return len(filas)
