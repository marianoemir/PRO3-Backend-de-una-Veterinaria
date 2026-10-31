# Diseño: fundacion-proyecto

## 1. Estructura de directorios

Según `knowledge-base/08_arquitectura_propuesta.md`:

```
PRO3-Backend-de-una-Veterinaria/
├── app/
│   ├── main.py                  # Aplicación FastAPI, lifespan y registro de routers
│   ├── core/
│   │   ├── __init__.py          # Vacío
│   │   ├── config.py            # Lectura de DATABASE_URL desde el entorno
│   │   └── database.py          # Dependencia get_session (toma sessionmaker de app.state)
│   └── modules/
│       ├── health/
│       │   ├── __init__.py
│       │   ├── models.py        # Stub vacío
│       │   ├── schemas.py       # Stub vacío
│       │   ├── service.py       # Stub vacío
│       │   └── router.py        # GET /health/live y GET /health/ready
│       ├── duenios/
│       │   ├── __init__.py      # Vacío
│       │   ├── models.py        # Stub vacío
│       │   ├── schemas.py       # Stub vacío
│       │   ├── service.py       # Stub vacío
│       │   └── router.py        # Stub: `router = APIRouter()`
│       ├── mascotas/            # Igual: __init__, models, schemas, service, router
│       ├── practicas/           # Ídem
│       ├── turnos/              # Ídem
│       └── laboratorio/         # Ídem
├── requirements.txt
├── env.example
└── .gitignore                   # Ya debe existir (heredado o creado)
```

**Justificación**: la estructura modular por funcionalidad es la que exige la consigna y se detalla en `08_arquitectura_propuesta.md`. Cada módulo repite el mismo patrón (`models.py`, `schemas.py`, `service.py`, `router.py`). En esta fundación se crean los 5 archivos por módulo como stubs vacíos (health/router.py además tiene los endpoints reales; el resto de sus archivos son stubs vacíos). Los stubs permiten que `main.py` importe todos los módulos sin error, y cada change posterior completa solo los archivos de su módulo.

## 2. app/core/config.py

Carga variables de entorno desde `.env` con `python-dotenv`. Expone `DATABASE_URL` como atributo obligatorio.

**Comportamiento esperado**:
- Si `DATABASE_URL` está definida (en el entorno o en `.env`), el arranque continúa.
- Si **no** está definida, el arranque falla con `sys.exit(1)` y un mensaje claro:
  `"FATAL: DATABASE_URL no está definida. Copiá env.example a .env y configurá la conexión."`

**Justificación** (RN-24, `knowledge-base/08_arquitectura_propuesta.md` §Variables de entorno): la cadena de conexión es sensible y no se versiona. El `env.example` muestra la forma del valor sin secretos. `sys.exit(1)` corta el proceso inmediatamente — sin base la app no puede operar, y un fallo temprano es más claro que un error críptico en el primer `SELECT`.

## 3. app/core/database.py

`database.py` **no** crea engine ni sessionmaker a nivel módulo. Solo expone la dependencia `get_session` que los toma de `app.state` (donde los guarda el `lifespan` de `main.py`).

```python
from fastapi import Request

async def get_session(request: Request):
    """Toma el async_sessionmaker de app.state, crea una sesión y la cierra al terminar."""
    async with request.app.state.session_local() as session:
        yield session
```

- **`expire_on_commit=False`** (RN-21): evita que SQLAlchemy invalide los objetos tras el commit, permitiendo acceder a atributos fuera de la sesión sin disparar carga perezosa (que fallaría con `MissingGreenlet` en modo async).
- **`echo=True`** en el engine: necesario para la evidencia del caso C-07 (fragmento de consola con consultas SQL del detalle de turno). Se configura en el `lifespan` de `main.py`, no acá.

## 4. app/main.py — Ciclo de vida (lifespan)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    session_local = async_sessionmaker(engine, expire_on_commit=False)
    app.state.engine = engine
    app.state.session_local = session_local
    yield
    await engine.dispose()
```

- **Sin `create_all`** (DD-01, `knowledge-base/09_decisiones_y_supuestos.md`): el esquema se crea desde `reiniciar.py` (change [09]).
- El motor se **cierra** al apagar para liberar el pool de conexiones.
- Se registran los 6 routers: `health`, `duenios`, `mascotas`, `practicas`, `turnos`, `laboratorio`. Cada uno se importa desde `app.modules.<módulo>.router`.

## 5. Módulo health — Endpoints de salud

### `GET /health/live`
- `async def`
- 200 `{"estado": "vivo"}`
- **No toca la base** (RN-22)

**Justificación**: un liveness check debe indicar si el proceso está vivo, independientemente del estado de la base. Si la base está caída, la app sigue viva y puede reportar su estado.

### `GET /health/ready`
- `async def`
- Ejecuta `SELECT 1` contra PostgreSQL.
- 200 `{"estado": "listo", "base": "ok"}` si responde.
- 503 `{"estado": "no_disponible", "base": "error"}` si falla.
- Atrapa `Exception` genérico (no solo SQLAlchemyError) porque asyncpg puede lanzar `ConnectionRefusedError`/`OSError` sin envolver.

**Justificación** (DD-14, `knowledge-base/09_decisiones_y_supuestos.md`): el readiness check distingue entre "app viva" y "app lista para recibir tráfico". Si la base no responde, la app no puede procesar requests que requieran persistencia, así que responde 503 para que un balanceador no le envíe tráfico.

## 6. Stubs de módulos

Cada módulo (incluyendo `health`) tiene 5 archivos, aunque `health` se crea en dos tareas:
- `__init__.py` vacío → `app.modules.<módulo>` es un paquete Python.
- `models.py` vacío → se completa en `modelos-y-esquema` [02].
- `schemas.py` vacío → se completa en el change del módulo correspondiente.
- `service.py` vacío → se completa en el change del módulo correspondiente.
- `router.py` con `router = APIRouter()` (salvo `health`, cuyo router se crea en la tarea 1.5 con los endpoints reales).

**Justificación**: todos los módulos siguen el mismo patrón (`models`, `schemas`, `service`, `router`). Tener los stubs desde la fundación evita errores de importación en `main.py` y permite que cada change toque solo su módulo.

## 7. requirements.txt

```
fastapi[standard]>=0.111
sqlmodel>=0.0.24
sqlalchemy[asyncio]>=2.0
asyncpg>=0.30
python-dotenv>=1.0
```

**Justificación** (`knowledge-base/02_descripcion_general.md` §Stack tecnológico y `knowledge-base/08_arquitectura_propuesta.md` §Dependencias): son las versiones mínimas del stack impuesto por la consigna. `fastapi[standard]` incluye uvicorn. `sqlalchemy[asyncio]` es necesario para el driver async.

## 8. env.example

```
DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria
```

**Justificación** (RN-24): el `.env` real no se versiona. El ejemplo muestra la forma exacta del valor para que cualquier desarrollador lo copie y configure su conexión local.

## Decisiones de dominio aplicadas

| Decisión | Referencia | Aplicación en este change |
|---|---|---|
| DD-01 — Sin `create_all` en el arranque | `09_decisiones_y_supuestos.md` | `main.py` no llama a `create_all`. Lo hará `reiniciar.py` en [09]. |
| DD-14 — Códigos de `/health/ready` | `09_decisiones_y_supuestos.md` | 200 con `{"estado": "listo", "base": "ok"}`, 503 con `{"estado": "no_disponible", "base": "error"}`. |