"""HU-001 Registro de cliente (CU-01) y HU-002 Inicio de sesión (CU-02)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import usuario_actual
from app.errores import ErrorNegocio
from app.models import Carrito, Monedero, Perfil, Rol, Usuario
from app.schemas import Credenciales, RegistroCliente, Token, UsuarioDetalle, UsuarioSalida
from app.security import cifrar_contrasena, crear_token, verificar_contrasena

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def detalle_usuario(usuario: Usuario) -> UsuarioDetalle:
    return UsuarioDetalle(
        id=usuario.id,
        nombre_usuario=usuario.nombre_usuario,
        rol=usuario.rol,
        perfil=usuario.perfil,
        perfil_completo=usuario.perfil is not None,
    )


@router.post("/registro", response_model=UsuarioDetalle, status_code=status.HTTP_201_CREATED)
def registrar_cliente(datos: RegistroCliente, db: Session = Depends(get_db)):
    """Crea la cuenta con rol cliente, su perfil, su monedero y su carrito (RF-28, RF-30, RF-61)."""
    if db.get(Perfil, datos.documento) is not None:
        raise ErrorNegocio(
            409,
            "DOCUMENTO_REGISTRADO",
            "Ya existe una cuenta con ese documento. Inicia sesión.",
            "documento",
        )
    if db.scalar(select(Usuario).where(Usuario.nombre_usuario == datos.nombre_usuario)):
        raise ErrorNegocio(
            409, "USUARIO_EN_USO", "Ese usuario ya está en uso. Escoge otro.", "nombre_usuario"
        )

    usuario = Usuario(
        nombre_usuario=datos.nombre_usuario,
        contrasena_hash=cifrar_contrasena(datos.contrasena),
        rol=Rol.CLIENTE,
    )
    db.add(usuario)
    db.flush()
    campos = datos.model_dump(exclude={"nombre_usuario", "contrasena"})
    usuario.perfil = Perfil(usuario_id=usuario.id, **campos)
    db.add_all([Monedero(cliente_id=usuario.id), Carrito(cliente_id=usuario.id)])
    db.commit()
    db.refresh(usuario)
    return detalle_usuario(usuario)


@router.post("/login", response_model=Token)
def iniciar_sesion(cred: Credenciales, db: Session = Depends(get_db)):
    """El root ingresa con su Id; los demás con su usuario (RF-31)."""
    usuario = db.scalar(select(Usuario).where(Usuario.nombre_usuario == cred.nombre_usuario))
    if (
        usuario is None
        or not usuario.activo
        or not verificar_contrasena(cred.contrasena, usuario.contrasena_hash)
    ):
        raise ErrorNegocio(401, "CREDENCIALES_INVALIDAS", "Usuario o contraseña incorrectos.")
    return Token(
        access_token=crear_token(str(usuario.id), usuario.rol, usuario.nombre_usuario),
        usuario=UsuarioSalida.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioDetalle)
def quien_soy(usuario: Usuario = Depends(usuario_actual)):
    return detalle_usuario(usuario)
