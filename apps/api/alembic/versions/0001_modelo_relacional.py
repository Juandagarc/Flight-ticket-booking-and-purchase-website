"""Modelo relacional completo (modelo E-R v1.0, 02/10/2026).

Ejecuta tal cual el script del anexo del documento «Modelo entidad-relación»: las 32 tablas,
las restricciones de la sección 5, las dos configuraciones de cabina con sus 400 sillas, las
cinco causales de fuerza mayor y el usuario root.

Revision ID: 0001
Revises:
"""

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCRIPT = Path(__file__).resolve().parents[2] / "sql" / "0001_modelo_relacional.sql"

TABLAS = [
    "recomendacion",
    "actividad_usuario",
    "mensaje_chatbot",
    "conversacion_chatbot",
    "mensaje",
    "conversacion",
    "notificacion",
    "suscripcion",
    "noticia",
    "cambio_silla",
    "pasabordo",
    "checkin",
    "afectacion_vuelo",
    "reembolso",
    "tiquete",
    "pasajero",
    "reserva",
    "carrito",
    "pago",
    "movimiento_monedero",
    "tarjeta",
    "monedero",
    "cancelacion_vuelo",
    "causal_fuerza_mayor",
    "promocion",
    "tarifa",
    "vuelo",
    "silla",
    "configuracion_cabina",
    "ciudad",
    "perfil",
    "usuario",
]


def upgrade() -> None:
    # Se usa el cursor del driver para que el script corra completo y sin interpretar «%».
    conexion = op.get_bind().connection.driver_connection
    with conexion.cursor() as cur:
        cur.execute(SCRIPT.read_text(encoding="utf-8"))


def downgrade() -> None:
    for tabla in TABLAS:
        op.execute(f"DROP TABLE IF EXISTS {tabla} CASCADE")
