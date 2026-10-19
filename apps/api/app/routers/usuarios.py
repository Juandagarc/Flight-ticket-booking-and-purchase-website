"""HU-003 Gestión del perfil (CU-03) y HU-004 Cambio de contraseña (CU-04)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_cliente, requiere_rol, usuario_actual
from app.errores import ErrorNegocio
from app.models import ActividadUsuario, Perfil, Rol, Usuario
from app.schemas import (
    ActividadSalida,
    CambioContrasena,
    DatosPerfilEditables,
    PerfilNuevo,
    PerfilSalida,
)
from app.security import cifrar_contrasena, verificar_contrasena

router = APIRouter(prefix="/usuarios/me", tags=["Perfil"])

# El root solo tiene Id y contraseña (RF-31): no tiene perfil.
_con_perfil = requiere_rol(Rol.CLIENTE, Rol.ADMINISTRADOR)


@router.get("/perfil", response_model=PerfilSalida)
def ver_perfil(usuario: Usuario = Depends(_con_perfil)):
    if usuario.perfil is None:
        raise ErrorNegocio(404, "PERFIL_INCOMPLETO", "Todavía no has completado tu perfil.")
    return usuario.perfil


@router.post("/perfil", response_model=PerfilSalida, status_code=status.HTTP_201_CREATED)
def completar_perfil(
    datos: PerfilNuevo,
    usuario: Usuario = Depends(requiere_rol(Rol.ADMINISTRADOR)),
    db: Session = Depends(get_db),
):
    """El administrador completa su registro con los mismos campos de un cliente (RF-32).

    Completar el perfil no le habilita compras ni reservas (RF-34).
    """
    if usuario.perfil is not None:
        raise ErrorNegocio(409, "PERFIL_EXISTENTE", "Tu perfil ya está registrado; edítalo.")
    if db.get(Perfil, datos.documento) is not None:
        raise ErrorNegocio(
            409, "DOCUMENTO_REGISTRADO", "Ese documento ya pertenece a otra cuenta.", "documento"
        )
    perfil = Perfil(usuario_id=usuario.id, **datos.model_dump())
    usuario.perfil = perfil
    db.commit()
    return perfil


@router.put("/perfil", response_model=PerfilSalida)
def editar_perfil(
    datos: DatosPerfilEditables,
    usuario: Usuario = Depends(_con_perfil),
    db: Session = Depends(get_db),
):
    """Actualiza los datos personales. El documento identifica la cuenta y no se edita."""
    perfil = usuario.perfil
    if perfil is None:
        raise ErrorNegocio(404, "PERFIL_INCOMPLETO", "Todavía no has completado tu perfil.")
    for campo, valor in datos.model_dump().items():
        setattr(perfil, campo, valor)
    db.commit()
    return perfil


@router.put("/contrasena", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_contrasena(
    datos: CambioContrasena,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    """Todo usuario autenticado, incluido el root, cambia su contraseña (RF-31, RF-62)."""
    if not verificar_contrasena(datos.actual, usuario.contrasena_hash):
        raise ErrorNegocio(400, "CONTRASENA_ACTUAL_INCORRECTA", "La contraseña actual no coincide.", "actual")
    if datos.nueva != datos.confirmacion:
        raise ErrorNegocio(
            400,
            "CONFIRMACION_NO_COINCIDE",
            "La nueva contraseña y su confirmación no coinciden.",
            "confirmacion",
        )
    usuario.contrasena_hash = cifrar_contrasena(datos.nueva)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/actividad", response_model=list[ActividadSalida])
def mi_actividad(
    limite: int = 20,
    usuario: Usuario = Depends(requiere_cliente),
    db: Session = Depends(get_db),
):
    """Búsquedas recientes del cliente (CU-21), insumo del recomendador (RF-60)."""
    return db.scalars(
        select(ActividadUsuario)
        .where(ActividadUsuario.cliente_id == usuario.id)
        .order_by(ActividadUsuario.fecha.desc())
        .limit(min(max(limite, 1), 100))
    ).all()
