# Flight · Sistema de gestión de compra y reserva de tiquetes aéreos en línea

Proyecto del Laboratorio de Software 2026-02 · Universidad Tecnológica de Pereira.
Equipo: Juan David García Arce, Juan David Cortés, Diego Alejandro Ascencio. Docente y cliente: Cesar Augusto Jaramillo.

Estado: **iteración 1 (HU-001 a HU-009) construida y probada**. El detalle de lo entregado y de cómo se probó cada criterio de aceptación está en [`docs/iteracion-1.md`](docs/iteracion-1.md).

## Stack (Anexo B de los requisitos)

| Parte | Tecnología |
| --- | --- |
| Monorepo | Turborepo + pnpm workspaces |
| API | FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 16 (`apps/api`) |
| Web | Next.js 15 (App Router) · TypeScript · Tailwind CSS 4 (`apps/web`) |
| Pruebas | pytest (API), Vitest (web), Playwright (extremo a extremo) |
| Entrega | Docker por aplicación · `docker-compose.yml` · GitHub Actions |

```
apps/
  api/   FastAPI: routers por módulo, reglas en app/services, migraciones Alembic, pruebas por HU
  web/   Next.js: páginas por pantalla de la maqueta, acciones de servidor, pruebas unitarias y e2e
docs/    Documentación de la iteración
```

## Arranque rápido con Docker

```bash
cp .env.example .env        # cambia ROOT_PASSWORD y JWT_SECRET
docker compose up --build
```

- Web: http://localhost:3000
- API y documentación interactiva: http://localhost:8000/docs
- Usuario root: `root` con la contraseña de `ROOT_PASSWORD` (se aplica la primera vez que arranca la API).

## Desarrollo local

Requisitos: Node 22 con pnpm 10, Python 3.13 con [uv](https://docs.astral.sh/uv/) y un PostgreSQL 16.

```bash
pnpm install
cd apps/api && uv sync && cp .env.example .env && cd ../..
cp apps/web/.env.example apps/web/.env.local
pnpm dev                    # API en :8000 (aplica migraciones) y web en :3000
```

## Pruebas

```bash
pnpm test                   # pytest de la API y Vitest de la web (vía Turborepo)
pnpm lint && pnpm typecheck

# Extremo a extremo: levanta la API y la web y recorre las 9 historias en Chromium.
createdb tiquetes_e2e
pnpm --filter @tiquetes/web build
pnpm --filter @tiquetes/web e2e
```

La API se prueba contra un PostgreSQL real: `TEST_DATABASE_URL` (por defecto
`postgresql+psycopg://postgres:postgres@localhost:5432/tiquetes_test`) indica el servidor; la base de pruebas se
recrea en cada corrida. Las pruebas e2e usan `E2E_DATABASE_URL` (por defecto la base `tiquetes_e2e`).

## Base de datos

La migración `0001` ejecuta tal cual el script SQL del documento «Modelo entidad-relación» (32 tablas, restricciones,
400 sillas, causales de fuerza mayor y el usuario root). La `0002` carga el catálogo de 37 ciudades y la secuencia
del código de vuelo.

```bash
cd apps/api && uv run alembic upgrade head
```
