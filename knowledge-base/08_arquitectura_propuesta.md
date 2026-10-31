# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|---|---|---|
| Por módulo funcional | `app/modules/<módulo>/{models,schemas,service,router}.py` | La consigna exige la misma estructura en todos los módulos; facilita repartir el trabajo |
| Separación modelo de tabla / DTO | `models.py` vs `schemas.py` | Objetivo 2: no exponer el modelo persistido ni aceptar `id` en las altas |
| Service con sesión inyectada | `service.py` recibe `AsyncSession` como parámetro | La lógica no conoce FastAPI; testeable y reutilizable |
| Dependencia por petición | `Depends(get_session)` | Una sesión por request, cerrada al terminar |
| Ciclo de vida de recursos | `lifespan` + `app.state` | El motor se crea y se cierra una sola vez |
| Fail-fast en la base | `IntegrityError` → rollback → 409 | Evita la ventana de carrera de "preguntar y después escribir" |
| Carga anticipada explícita | `joinedload` / `selectinload` | Evita N+1 y `MissingGreenlet` en asincronía |
| Offloading de bloqueo | Biblioteca sincrónica fuera del event loop | Un handler `async def` no debe bloquear |

## Estructura de directorios

```
PRO3-Backend-de-una-Veterinaria/
├── app/
│   ├── main.py                  Aplicación, lifespan y registro de routers
│   ├── core/
│   │   ├── config.py            Lectura de DATABASE_URL desde el entorno
│   │   └── database.py          Motor, fábrica de sesiones y dependencia get_session
│   └── modules/
│       ├── health/
│       ├── duenios/             incluye models.FichaDuenio
│       ├── mascotas/
│       ├── practicas/
│       ├── turnos/              incluye models.TurnoPractica
│       └── laboratorio/         cliente.py (biblioteca sincrónica) + router
├── test/                        archivos .http + .sql de casos
├── docs/                        enunciado fuente
├── knowledge-base/              esta KB
├── reiniciar.py
├── requirements.txt
├── env.example
├── .env                         NO versionado
└── README.md
```

Cada módulo repite:

```
app/modules/<módulo>/
├── models.py    Modelos de tabla, restricciones y relaciones
├── schemas.py   DTO de entrada (Create, Update) y de salida (Read)
├── service.py   Lógica, traducción de errores y lecturas con precarga
└── router.py    Rutas HTTP: reciben, delegan y declaran la respuesta
```

## Capas y dirección de dependencias

```
router.py  ──▶ service.py ──▶ models.py
   │              │
   └──▶ schemas.py└──▶ core/database.py ──▶ PostgreSQL
```

- `router.py` no contiene lógica de negocio.
- `service.py` no importa nada de FastAPI.
- `schemas.py` no conoce SQLAlchemy.
- `models.py` no conoce DTO de entrada.

## Seguridad

| Aspecto | Enfoque |
|---|---|
| Autenticación | **Fuera de alcance** (consigna) |
| Autorización | **Fuera de alcance** (consigna) |
| Validación de input | DTO de Pydantic/SQLModel + `CHECK`/`UNIQUE`/FK en la base. `ilike`/SQL crudo: **no** hay en el alcance |
| Secrets management | `DATABASE_URL` en `.env` no versionado; `env.example` sin secretos |
| Riesgo del repo | Credenciales reales en el repositorio descalifican la corrección hasta subsanarlo |

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | Cadena de conexión asincrónica a PostgreSQL | `postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria` | **Sí** |

## Dependencias

`requirements.txt` con, como mínimo, las versiones de [02_descripcion_general.md](02_descripcion_general.md): `fastapi[standard]>=0.111`, `sqlmodel>=0.0.24`, `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30`, `python-dotenv>=1.0`.

## Entregables del repositorio

Según "Formato de entrega":

- Código fuente completo.
- `requirements.txt`.
- `env.example`.
- `reiniciar.py`.
- Carpeta `test/`.
- `README.md` con los pasos para levantar el proyecto desde cero (entorno virtual, dependencias, `.env`, `python reiniciar.py`, arranque del servidor) y la explicación del índice de `turno_practica.turno_id`.
- Evidencia del caso C-07: fragmento de consola con las consultas del detalle de un turno con una práctica y con tres.
- `.env` **no** se sube.
