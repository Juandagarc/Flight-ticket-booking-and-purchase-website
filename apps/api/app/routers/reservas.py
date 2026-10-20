"""Barrera de acceso a reservar y comprar (RF-33, RF-34, RF-63).

La reserva y la compra se construyen en la iteración 2; desde ya, esta verificación es la que
usan la interfaz y las futuras rutas: un visitante debe registrarse o iniciar sesión, y un root
o administrador nunca puede reservar ni comprar.
"""

from fastapi import APIRouter, Depends

from app.deps import requiere_cliente
from app.models import Usuario

router = APIRouter(prefix="/reservas", tags=["Reserva y compra"])


@router.get("/acceso")
def acceso_a_reservar(usuario: Usuario = Depends(requiere_cliente)):
    return {"permitido": True, "usuario": usuario.nombre_usuario}
