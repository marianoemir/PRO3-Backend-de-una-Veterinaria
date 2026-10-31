# Propuesta: fundacion-proyecto

## Qué

Establecer la base del servicio **PRO3 — Backend de una Veterinaria** para que los tres desarrolladores puedan trabajar en paralelo sobre los módulos funcionales.

## Por qué

Sin la estructura base, ningún módulo puede arrancar. Este change sienta el scaffold completo: configuración, conexión a base, ciclo de vida, endpoints de salud y stubs de los 6 módulos. Es el change [01] del roadmap, sin dependencias previas.

## Alcance

| ¿Qué incluye? | ¿Qué queda fuera? |
|---|---|
| Estructura completa de directorios (`app/`, `app/core/`, `app/modules/<módulo>/`) | Modelos de datos (`models.py`) — los escribe `modelos-y-esquema` [02] |
| Configuración de base de datos (`config.py` + `database.py`) con ciclo de vida (lifespan) | DTOs, services y routers funcionales — cada módulo en su change |
| Endpoints de salud (`GET /health/live` y `GET /health/ready`) | `reiniciar.py` — lo escribe `reiniciar-y-seed` [09] |
| Stubs de los 6 módulos (`__init__.py`, `models.py`, `schemas.py`, `service.py` y `router.py` vacíos; `health/router.py` además tiene endpoints reales) | Tests y evidencia — los escribe `pruebas-http-y-evidencia` [10] |
| `requirements.txt`, `env.example`, `.gitignore` | README — lo escribe `readme-y-entrega` [11] |
| Sin `create_all` en el arranque (DD-01) | Auth, Docker, CI, Alembic, colas (fuera de alcance global) |

## Reglas de negocio cubiertas

- **RN-17**: todos los handlers `async def` — se aplica a `health/live` y `health/ready`
- **RN-20**: motor y fábrica en `lifespan`, guardados en `app.state`, cierre al apagar
- **RN-21**: sesión por petición vía `Depends(get_session)`, con `expire_on_commit=False`
- **RN-22**: `GET /health/live` no toca la base; `GET /health/ready` ejecuta `SELECT 1` y responde 503 si falla
- **RN-24**: `DATABASE_URL` desde el entorno, `env.example` sin secretos

## Dueño

**Mariano**. Este change es de su exclusiva responsabilidad (ver CHANGES.md - archivos compartidos).

## Dependencias

Ninguna. Este es el cambio raíz del proyecto.