# Tareas: fundacion-proyecto

> Dueño: **Mariano**. Duración estimada: **6–8 h**. Dependencias: ninguna.

---

### [x] 1.1 — Crear `app/core/__init__.py` vacío

Archivo vacío para que `app.core` sea un paquete Python.

**Verificación**: `python -c "import app.core; print('ok')"` muestra `ok`.

---

### [x] 1.2 — Crear `app/core/config.py` con carga de .env y fallo si falta DATABASE_URL

- Cargar `.env` con `python-dotenv` (`load_dotenv()`)
- Definir clase `Settings` con `DATABASE_URL: str`
- Validar que no sea `None` o vacío; si falta, imprimir `"FATAL: DATABASE_URL no está definida. Copiá env.example a .env y configurá la conexión."` y salir con `sys.exit(1)`
- Exportar una instancia `settings = Settings()` (singleton)

**Verificación**: `python -c "from app.core.config import settings; print(settings.DATABASE_URL)"`:
- Sin `.env` → falla con mensaje FATAL
- Con `.env` con `DATABASE_URL` → imprime la URL

---

### [x] 1.3 — Crear `app/core/database.py` con get_session desde app.state

- **No** crear engine ni sessionmaker a nivel módulo — los crea el `lifespan` en `main.py` y los guarda en `app.state`.
- `get_session(request: Request)` → función asíncrona generadora que toma el `async_sessionmaker` de `request.app.state.session_local`, crea una sesión, hace `yield`, y la cierra al salir del `async with`.
- La función recibe `request: Request` como parámetro de FastAPI (se vincula automáticamente).

```python
from fastapi import Request

async def get_session(request: Request):
    async with request.app.state.session_local() as session:
        yield session
```

**Verificación**: `python -c "import inspect; from app.core.database import get_session; print(inspect.isasyncgenfunction(get_session))"` debe imprimir `True`.

---

### [x] 1.4 — Crear `app/__init__.py` vacío

Archivo vacío para que `app` sea un paquete Python.

**Verificación**: `python -c "import app; print('ok')"` muestra `ok`.

---

### [x] 1.5 — Crear `app/modules/health/router.py` con GET /health/live y GET /health/ready

- `router = APIRouter(prefix="/health", tags=["health"])`
- `GET /live` → `async def`, retorna `{"estado": "vivo"}` con 200. No toca la base.
- `GET /ready` → `async def`, recibe sesión por `Depends(get_session)`. Ejecuta `await session.execute(text("SELECT 1"))`. Si funciona → `{"estado": "listo", "base": "ok"}` con 200. Si falla, atrapa `Exception` genérico (asyncpg puede lanzar `ConnectionRefusedError`/`OSError` sin envolver) y retorna `JSONResponse(status_code=503, content={"estado": "no_disponible", "base": "error"})`.
- Importar `from sqlalchemy import text` y `from fastapi.responses import JSONResponse`.

**Verificación**: con `uvicorn app.main:app`:
- `curl http://localhost:8000/health/live` → `{"estado": "vivo"}`
- `curl http://localhost:8000/health/ready` → `{"estado": "listo", "base": "ok"}` (con base arriba)
- `curl http://localhost:8000/health/ready` → `{"estado": "no_disponible", "base": "error"}` (con base abajo)

---

### [x] 1.6 — Crear stubs de módulos (__init__, models, schemas, service) para los 6 módulos

Para cada uno de los 6 módulos, crear los archivos vacíos que luego completará cada change:

| Archivo | Propósito | Lo completa |
|---------|-----------|-------------|
| `__init__.py` | Que el módulo sea un paquete Python | — (vacío siempre) |
| `models.py` | Modelos de tabla | `modelos-y-esquema` [02] |
| `schemas.py` | DTO de entrada/salida | Change del módulo |
| `service.py` | Lógica de negocio | Change del módulo |

**Nota**: `router.py` en `health` lo crea la tarea 1.5 con endpoints reales; para los otros 5 módulos se crea en esta tarea con `router = APIRouter()`.

**Módulos**: `health`, `duenios`, `mascotas`, `practicas`, `turnos`, `laboratorio`.

La estructura final debe ser:

```
app/modules/health/__init__.py         (vacio)
app/modules/health/models.py           (vacio)
app/modules/health/schemas.py          (vacio)
app/modules/health/service.py          (vacio)
# router.py ya lo creó la tarea 1.5

app/modules/duenios/__init__.py        (vacio)
app/modules/duenios/models.py          (vacio)
app/modules/duenios/schemas.py         (vacio)
app/modules/duenios/service.py         (vacio)
app/modules/duenios/router.py          (router = APIRouter())

... (mascotas, practicas, turnos, laboratorio: igual que duenios)
```

**Verificación**: en cada módulo (salvo health cuyo router ya existe), `python -c "from app.modules.<modulo>.router import router; print(type(router).__name__)"` debe mostrar `APIRouter`. Para health, verificar que `import app.modules.health.models` funciona sin error.

---

### [x] 1.7 — Crear `app/main.py` con lifespan, 6 routers importados, sin create_all

- Aplicación FastAPI con `lifespan`
- `lifespan` crea `engine = create_async_engine(settings.DATABASE_URL, echo=True)` y `session_local = async_sessionmaker(engine, expire_on_commit=False)`, los guarda en `app.state`, y en shutdown cierra el engine con `await engine.dispose()`
- NO llama a `create_all` (DD-01)
- Incluye:
  - `app.include_router(health.router)`
  - `app.include_router(duenios.router)`
  - `app.include_router(mascotas.router)`
  - `app.include_router(practicas.router)`
  - `app.include_router(turnos.router)`
  - `app.include_router(laboratorio.router)`

**Verificación**: `uvicorn app.main:app` levanta sin errores. `/openapi.json` muestra las rutas de `health` (`/health/live` y `/health/ready`); los otros 5 routers están registrados pero vacíos.

---

### [x] 1.8 — Crear `requirements.txt`

```
fastapi[standard]>=0.111
sqlmodel>=0.0.24
sqlalchemy[asyncio]>=2.0
asyncpg>=0.30
python-dotenv>=1.0
```

**Verificación**: `pip install -r requirements.txt` instala sin errores.

---

### [x] 1.9 — Crear `env.example`

```
DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/veterinaria
```

**Verificación**: el archivo contiene la forma del valor sin secretos reales. `usuario` y `clave` son placeholders.

---

### [x] 1.10 — Verificar .gitignore incluye .env

- Si no existe `.gitignore`, crearlo con al menos `.env` en su contenido.
- Si existe, verificar que `.env` esté listado.

**Verificación**: `git check-ignore .env` debe mostrar `.env` (el archivo está siendo ignorado por git).

---

### [ ] 1.11 — Probar /health/ready con 503 deteniendo PostgreSQL

- Iniciar la app con `uvicorn app.main:app` (con base funcionando).
- Verificar que `/health/ready` responde 200.
- Detener el servicio de PostgreSQL: `net stop postgresql-x64-17` (ejecutar como administrador).
- Consultar `/health/ready` → debe responder 503 `{"estado": "no_disponible", "base": "error"}`.
- Consultar `/health/live` → debe seguir respondiendo 200 `{"estado": "vivo"}` (la app sigue viva).
- Reiniciar el servicio: `net start postgresql-x64-17`.
- Volver a consultar `/health/ready` → debe responder 200 nuevamente.

**Verificación**: secuencia completa de comandos anterior. El handler atrapa `Exception` genérico alrededor de `execute(text("SELECT 1"))` y retorna `JSONResponse(status_code=503)`.

---

## Resumen de verificación final (smoke)

1. `pip install -r requirements.txt` → exitoso
2. Copiar `env.example` a `.env` y configurar con una base real
3. `uvicorn app.main:app` → servidor levantado sin errores
4. `GET /health/live` → 200
5. `GET /health/ready` → 200
6. `GET /openapi.json` → 200, con rutas de `/health/live` y `/health/ready`; los otros 5 routers registrados pero vacíos
7. Sin `.env` → arranque falla con mensaje FATAL
8. `git check-ignore .env` → `.env` ignorado
9. Detener PostgreSQL (`net stop postgresql-x64-17`), `/health/ready` → 503, `/health/live` sigue en 200, reiniciar PostgreSQL (`net start postgresql-x64-17`), `/health/ready` → 200 de nuevo