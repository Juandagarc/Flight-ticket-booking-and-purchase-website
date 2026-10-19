"""Catálogo de ciudades y consecutivo del código de vuelo.

- Las 32 capitales departamentales (RF-03, RF-49), con Pereira, Bogotá, Medellín, Cali y
  Cartagena marcadas como orígenes internacionales (RF-04).
- Los 5 destinos internacionales: Madrid, Londres, New York, Buenos Aires y Miami (RF-05).
- Zona horaria IANA para la hora local de llegada (RF-02) y coordenadas para calcular la
  distancia y el tiempo de vuelo (RF-53).
- La secuencia que da el consecutivo del código de vuelo FL0001, FL0002… (RF-54).

Los códigos de ciudad son los IATA del aeropuerto o de la ciudad; Tunja, sin aeropuerto
comercial, usa TUN.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

BOGOTA = "America/Bogota"

# codigo, nombre, departamento o país, zona, latitud, longitud, origen internacional
CAPITALES = [
    ("LET", "Leticia", "Amazonas", -4.215300, -69.940600, False),
    ("MDE", "Medellín", "Antioquia", 6.244200, -75.581200, True),
    ("AUC", "Arauca", "Arauca", 7.084700, -70.759100, False),
    ("BAQ", "Barranquilla", "Atlántico", 10.968500, -74.781300, False),
    ("CTG", "Cartagena", "Bolívar", 10.391000, -75.479400, True),
    ("TUN", "Tunja", "Boyacá", 5.535300, -73.367800, False),
    ("MZL", "Manizales", "Caldas", 5.070300, -75.513800, False),
    ("FLA", "Florencia", "Caquetá", 1.614400, -75.606200, False),
    ("EYP", "Yopal", "Casanare", 5.337800, -72.395900, False),
    ("PPN", "Popayán", "Cauca", 2.444800, -76.614700, False),
    ("VUP", "Valledupar", "Cesar", 10.463100, -73.253200, False),
    ("UIB", "Quibdó", "Chocó", 5.694700, -76.661100, False),
    ("MTR", "Montería", "Córdoba", 8.747900, -75.881400, False),
    ("BOG", "Bogotá", "Cundinamarca", 4.711000, -74.072100, True),
    ("PDA", "Inírida", "Guainía", 3.865300, -67.923900, False),
    ("SJE", "San José del Guaviare", "Guaviare", 2.572900, -72.645900, False),
    ("NVA", "Neiva", "Huila", 2.927300, -75.281900, False),
    ("RCH", "Riohacha", "La Guajira", 11.544400, -72.907200, False),
    ("SMR", "Santa Marta", "Magdalena", 11.240800, -74.199000, False),
    ("VVC", "Villavicencio", "Meta", 4.142000, -73.626600, False),
    ("PSO", "Pasto", "Nariño", 1.213600, -77.281100, False),
    ("CUC", "Cúcuta", "Norte de Santander", 7.893900, -72.507800, False),
    ("VGZ", "Mocoa", "Putumayo", 1.147800, -76.647500, False),
    ("AXM", "Armenia", "Quindío", 4.533900, -75.681100, False),
    ("PEI", "Pereira", "Risaralda", 4.813300, -75.696100, True),
    ("ADZ", "San Andrés", "San Andrés y Providencia", 12.584700, -81.700600, False),
    ("BGA", "Bucaramanga", "Santander", 7.119300, -73.122700, False),
    ("CZU", "Sincelejo", "Sucre", 9.304700, -75.397800, False),
    ("IBE", "Ibagué", "Tolima", 4.438900, -75.232200, False),
    ("CLO", "Cali", "Valle del Cauca", 3.451600, -76.532000, True),
    ("MVP", "Mitú", "Vaupés", 1.253700, -70.234000, False),
    ("PCR", "Puerto Carreño", "Vichada", 6.189000, -67.485900, False),
]

INTERNACIONALES = [
    ("MAD", "Madrid", "España", "Europe/Madrid", 40.416800, -3.703800),
    ("LON", "Londres", "Reino Unido", "Europe/London", 51.507400, -0.127800),
    ("NYC", "New York", "Estados Unidos", "America/New_York", 40.712800, -74.006000),
    ("BUE", "Buenos Aires", "Argentina", "America/Argentina/Buenos_Aires", -34.603700, -58.381600),
    ("MIA", "Miami", "Estados Unidos", "America/New_York", 25.761700, -80.191800),
]


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS vuelo_consecutivo START 1")
    ciudad = sa.table(
        "ciudad",
        sa.column("codigo"),
        sa.column("nombre"),
        sa.column("pais"),
        sa.column("zona_horaria"),
        sa.column("latitud"),
        sa.column("longitud"),
        sa.column("es_capital_nacional"),
        sa.column("origen_internacional"),
        sa.column("destino_internacional"),
    )
    filas = [
        {
            "codigo": c,
            "nombre": n,
            "pais": "Colombia",
            "zona_horaria": BOGOTA,
            "latitud": lat,
            "longitud": lon,
            "es_capital_nacional": True,
            "origen_internacional": oi,
            "destino_internacional": False,
        }
        for c, n, _dep, lat, lon, oi in CAPITALES
    ] + [
        {
            "codigo": c,
            "nombre": n,
            "pais": p,
            "zona_horaria": z,
            "latitud": lat,
            "longitud": lon,
            "es_capital_nacional": False,
            "origen_internacional": False,
            "destino_internacional": True,
        }
        for c, n, p, z, lat, lon in INTERNACIONALES
    ]
    op.bulk_insert(ciudad, filas)


def downgrade() -> None:
    op.execute("DELETE FROM ciudad")
    op.execute("DROP SEQUENCE IF EXISTS vuelo_consecutivo")
