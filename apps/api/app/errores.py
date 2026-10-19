"""Errores de negocio con un código estable y un mensaje en español para la interfaz."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorNegocio(Exception):
    def __init__(self, estado: int, codigo: str, mensaje: str, campo: str | None = None):
        self.estado = estado
        self.codigo = codigo
        self.mensaje = mensaje
        self.campo = campo


def _respuesta(estado: int, codigo: str, mensaje: str, campos: list[dict] | None = None):
    cuerpo: dict = {"codigo": codigo, "mensaje": mensaje}
    if campos:
        cuerpo["campos"] = campos
    return JSONResponse(status_code=estado, content={"detail": cuerpo})


async def manejar_error_negocio(_: Request, exc: ErrorNegocio):
    campos = [{"campo": exc.campo, "mensaje": exc.mensaje}] if exc.campo else None
    return _respuesta(exc.estado, exc.codigo, exc.mensaje, campos)


_MENSAJES = {
    "missing": "Este dato es obligatorio.",
    "string_too_short": "Este dato es obligatorio.",
    "string_too_long": "El valor es demasiado largo.",
    "string_pattern_mismatch": "El formato no es válido.",
    "value_error": "El valor no es válido.",
    "literal_error": "Escoge una de las opciones permitidas.",
    "date_from_datetime_parsing": "La fecha no es válida.",
    "date_parsing": "La fecha no es válida.",
    "time_parsing": "La hora no es válida.",
    "decimal_parsing": "Debe ser un número.",
    "greater_than": "Debe ser mayor que cero.",
    "extra_forbidden": "Este dato no se puede modificar.",
    "int_parsing": "Debe ser un número entero.",
}

_MENSAJES_CAMPO = {
    "documento": "El documento debe ser alfanumérico, de 4 a 20 caracteres, sin espacios.",
    "correo": "El correo no es válido.",
    "nombre_usuario": "El usuario debe tener de 3 a 50 caracteres: letras, números, punto, guion o guion bajo.",
}


async def manejar_validacion(_: Request, exc: RequestValidationError):
    campos = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
        campo = ".".join(loc) or "solicitud"
        tipo = err.get("type", "")
        if tipo == "missing" or tipo == "string_too_short":
            mensaje = _MENSAJES[tipo]
        elif campo in _MENSAJES_CAMPO and tipo not in ("extra_forbidden",):
            mensaje = _MENSAJES_CAMPO[campo]
        elif tipo == "value_error" and err.get("ctx", {}).get("error"):
            mensaje = str(err["ctx"]["error"])
        else:
            mensaje = _MENSAJES.get(tipo, err.get("msg", "Dato inválido."))
        campos.append({"campo": campo, "mensaje": mensaje})
    return _respuesta(422, "DATOS_INVALIDOS", "Revisa los datos marcados.", campos)
