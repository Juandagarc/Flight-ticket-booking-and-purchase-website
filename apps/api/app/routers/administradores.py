"""HU-005 Creación de administradores (CU-05). Solo el root (RF-31)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import requiere_root
from app.errores import ErrorNegocio
from app.models import Rol, Usuario
from app.schemas import AdministradorNuevo, AdministradorSalida
from app.security import cifrar_contrasena

router = APIRouter(prefix="/administradores", tags=["Administradores"])


@router.get("", response_model=list[AdministradorSalida])
def listar_administradores(_: Usuario = Depends(requiere_root), db: Session = Depends(get_db)):
    return db.scalars(
        select(Usuario).where(Usuario.rol == Rol.ADMINISTRADOR).order_by(Usuario.fecha_creacion)
    ).all()


@router.post("", response_model=AdministradorSalida, status_code=status.HTTP_201_CREATED)
def crear_administrador(
    datos: AdministradorNuevo,
    _: Usuario = Depends(requiere_root),
    db: Session = Depends(get_db),
):
    if db.scalar(select(Usuario).where(Usuario.nombre_usuario == datos.nombre_usuario)):
        raise ErrorNegocio(409, "USUARIO_EN_USO", "Ya existe una cuenta con ese usuario.", "nombre_usuario")
    admin = Usuario(
        nombre_usuario=datos.nombre_usuario,
        contrasena_hash=cifrar_contrasena(datos.contrasena),
        rol=Rol.ADMINISTRADOR,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
