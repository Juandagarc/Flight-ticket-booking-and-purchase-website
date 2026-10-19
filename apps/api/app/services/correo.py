"""Envío de correo (RNF-03). Con SMTP configurado envía de verdad; si no, deja el correo en el log.

Las pruebas reemplazan el enviador con `usar_enviador()` para inspeccionar lo enviado.
"""

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.config import get_settings

log = logging.getLogger("correo")


@dataclass
class Correo:
    para: str
    asunto: str
    cuerpo: str


class Enviador(Protocol):
    def enviar(self, correo: Correo) -> None: ...


class EnviadorLog:
    def enviar(self, correo: Correo) -> None:
        log.info("Correo a %s · %s\n%s", correo.para, correo.asunto, correo.cuerpo)


class EnviadorSmtp:
    def enviar(self, correo: Correo) -> None:
        s = get_settings()
        msg = EmailMessage()
        msg["From"] = s.smtp_remitente
        msg["To"] = correo.para
        msg["Subject"] = correo.asunto
        msg.set_content(correo.cuerpo)
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as smtp:
            if s.smtp_tls:
                smtp.starttls()
            if s.smtp_usuario:
                smtp.login(s.smtp_usuario, s.smtp_contrasena or "")
            smtp.send_message(msg)


class EnviadorMemoria:
    """Guarda los correos en una lista; lo usan las pruebas."""

    def __init__(self) -> None:
        self.enviados: list[Correo] = []

    def enviar(self, correo: Correo) -> None:
        self.enviados.append(correo)


_enviador: Enviador | None = None


def obtener_enviador() -> Enviador:
    global _enviador
    if _enviador is None:
        _enviador = EnviadorSmtp() if get_settings().smtp_host else EnviadorLog()
    return _enviador


def usar_enviador(enviador: Enviador | None) -> None:
    global _enviador
    _enviador = enviador
