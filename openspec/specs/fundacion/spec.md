# fundacion Specification

## Purpose
Establecer la base del servicio FastAPI: estructura de directorios, configuración de base de datos con ciclo de vida (lifespan), endpoints de salud, stubs de los 6 módulos funcionales y dependencias. Sin este cambio ningún módulo puede arrancar.

## Requirements

### Requirement: GET /health/live

**SHALL** responder `{"estado": "vivo"}` con HTTP 200 sin tocar la base de datos.

#### Scenario: Liveness exitoso con base disponible

| Dato | Valor |
|---|---|
| **Dado** | PostgreSQL está corriendo y la app está levantada con `uvicorn app.main:app` |
| **Cuando** | Se envía `GET /health/live` |
| **Entonces** | Responde **200** con `{"estado": "vivo"}` |

#### Scenario: Liveness exitoso con base caída

| Dato | Valor |
|---|---|
| **Dado** | PostgreSQL está detenido (servicio `postgresql-x64-17` detenido) y la app está levantada |
| **Cuando** | Se envía `GET /health/live` |
| **Entonces** | Responde **200** con `{"estado": "vivo"}` (la app sigue viva aunque la base no responda) |

### Requirement: GET /health/ready

**SHALL** ejecutar `SELECT 1` contra PostgreSQL y responder **200** con `{"estado": "listo", "base": "ok"}` si la base responde, o **503** con `{"estado": "no_disponible", "base": "error"}` si la base no responde.

#### Scenario: Readiness exitoso con base disponible

| Dato | Valor |
|---|---|
| **Dado** | PostgreSQL está corriendo, `DATABASE_URL` correcta en `.env`, app levantada |
| **Cuando** | Se envía `GET /health/ready` |
| **Entonces** | Responde **200** con `{"estado": "listo", "base": "ok"}` |

#### Scenario: Readiness 503 con base detenida

| Dato | Valor |
|---|---|
| **Dado** | PostgreSQL está detenido (servicio `postgresql-x64-17` detenido) y la app está levantada |
| **Cuando** | Se envía `GET /health/ready` |
| **Entonces** | El handler atrapa `Exception` (asyncpg puede lanzar `ConnectionRefusedError`/`OSError` sin envolver) y responde **503** con `{"estado": "no_disponible", "base": "error"}` |

### Requirement: DATABASE_URL ausente

**SHALL** fallar el arranque con `sys.exit(1)` y un mensaje claro si `DATABASE_URL` no está definida en el entorno ni en `.env`.

#### Scenario: Arranque sin DATABASE_URL

| Dato | Valor |
|---|---|
| **Dado** | No existe `DATABASE_URL` en variables de entorno ni en `.env` |
| **Cuando** | Se ejecuta `uvicorn app.main:app` |
| **Entonces** | El proceso termina con un mensaje que contiene `"FATAL"` y `"DATABASE_URL"` |
| **Y** | El servidor no escucha en ningún puerto |

### Requirement: OpenAPI expone las rutas de health

**SHALL** exponer el schema OpenAPI en `/openapi.json`. Los routers de los 6 módulos están registrados; `health` expone las rutas `/health/live` y `/health/ready`; los otros 5 routers están registrados sin rutas.

#### Scenario: OpenAPI expone las rutas

| Dato | Valor |
|---|---|
| **Dado** | La app está levantada |
| **Cuando** | Se envía `GET /openapi.json` |
| **Entonces** | Responde **200** y el schema incluye las rutas `/health/live` y `/health/ready` (los otros 5 routers están registrados sin rutas) |
