# Tareas: practicas-catalogo

> Dueño: **Andrés**. Duración estimada total: **3–4 h**. Dependencias: `02` `modelos-y-esquema` (archivado).
> Alcance: **solo `app/modules/practicas/{schemas,service,router}.py`**. No se toca `models.py`, `app/main.py` ni `reiniciar.py`.

## Notas previas (leer antes de empezar)

- **La base debe existir** para el smoke: correr `python reiniciar.py` (change [09], archivado) antes de levantar la app. Sin base, `GET /practicas/` responde 500 al conectar.
- **`app/main.py` ya registra el router** de `practicas` (change [01]); no se edita. El router declara su propio `prefix="/practicas"`.
- **Sin `psql`**: la verificación se hace con la app levantada (`uvicorn app.main:app`) y peticiones HTTP (`.http` o curl), más consultas en pgAdmin si hiciera falta.
- **TDD**: no hay suite pytest obligatoria. Cada tarea se verifica con una petición HTTP observable o con el intérprete Python (import + validación de Pydantic).

## 1. DTOs (`schemas.py`)

- [x] **1.1 — `PracticaCreate`** *(30 min)*
  - `nombre: str` (obligatorio) y `precio: Decimal = Field(gt=0)`. **Sin `id`** (RN-10).
  - Importar `Decimal` de `decimal` y `Field` de `pydantic`.
  - **Verificación**: `python -c "from app.modules.practicas.schemas import PracticaCreate; from decimal import Decimal; PracticaCreate(nombre='X', precio=Decimal('10'))"` no lanza; `PracticaCreate(nombre='X', precio=Decimal('0'))` lanza `ValidationError` (precio ≤ 0); `PracticaCreate(nombre='X', precio=Decimal('-1'))` lanza `ValidationError`.

- [x] **1.2 — `PracticaRead` con precio como string** *(30 min)*
  - `id: int`, `nombre: str`, `precio: Decimal` con `@field_serializer("precio")` que devuelve `f"{v:.2f}"` (string).
  - Configurar `model_config = ConfigDict(from_attributes=True)` para construir desde el modelo `Practica` (SQLModel/ORM).
  - **Verificación**: `PracticaRead.model_validate(Practica(id=1, nombre='X', precio=Decimal('15000.00'))).model_dump_json()` contiene `"precio":"15000.00"` (string con dos decimales), no un número.

## 2. Service (`service.py`)

- [x] **2.1 — `crear_practica(session, dto)`** *(45 min)*
  - Construir `Practica(nombre=dto.nombre, precio=dto.precio)`, `session.add(...)`, `await session.commit()`, `await session.refresh(practica)`, devolver la práctica.
  - Capturar `sqlalchemy.exc.IntegrityError`: `await session.rollback()` y lanzar `HTTPException(status_code=409, detail="Ya existe una práctica con ese nombre")`. **Sin `SELECT` previo** (DD-03).
  - Importar `AsyncSession`, `IntegrityError`, `HTTPException`.
  - **Verificación**: con la app levantada y la base reiniciada, `POST /practicas/` con `{"nombre":"Consulta","precio":"999.00"}` (nombre ya existente en el seed) responde **409** con mensaje propio; `POST /practicas/` con `{"nombre":"Practica Nueva","precio":"5000.00"}` responde **201** y la fila queda en `practica`.

- [x] **2.2 — `listar_practicas(session)`** *(20 min)*
  - `result = await session.execute(select(Practica).order_by(Practica.id))`; devolver `list(result.scalars().all())`. Una sola consulta, sin relaciones (DD-15).
  - **Verificación**: `GET /practicas/` responde **200** con el catálogo ordenado por `id` ascendente; con `echo=True` en la consola aparece **un solo `SELECT`** (evidencia de número fijo de consultas).

## 3. Router (`router.py`)

- [x] **3.1 — `POST /practicas/`** *(20 min)*
  - `APIRouter(prefix="/practicas", tags=["practicas"])`.
  - `@router.post("/", response_model=PracticaRead, status_code=201)` con handler `async def`, recibe `PracticaCreate` y `session: AsyncSession = Depends(get_session)`, delega a `crear_practica`.
  - **Verificación**: `POST /practicas/` con cuerpo válido → **201** y `PracticaRead` con `id`; cuerpo con `precio <= 0` → **422** (sin pasar por el service); nombre repetido → **409**.

- [x] **3.2 — `GET /practicas/`** *(15 min)*
  - `@router.get("/", response_model=list[PracticaRead])` con handler `async def`, delega a `listar_practicas`.
  - **Verificación**: `GET /practicas/` → **200** con arreglo; el primer elemento tiene `precio` como string con dos decimales.

## 4. Smoke de integración

- [x] **4.1 — Levantar la app y verificar el contrato completo** *(45 min)*
  - Ejecutar `python reiniciar.py` (base limpia) y luego `uvicorn app.main:app`.
  - Casos a ejecutar (con `.http` o curl):
    1. `POST /practicas/` `{"nombre":"Practica Smoke","precio":"5000.00"}` → **201**, `precio` sale como `"5000.00"`.
    2. Mismo body repetido → **409** con mensaje propio.
    3. `POST /practicas/` `{"nombre":"P","precio":0}` → **422**.
    4. `POST /practicas/` `{"nombre":"P","precio":-1}` → **422**.
    5. `GET /practicas/` → **200**, lista ordenada por `id`, todos los `precio` son strings con dos decimales.
  - **Verificación**: los 5 casos responden con los códigos esperados y el precio se serializa como string. Detener `uvicorn` al terminar.

- [x] **4.2 — Verificar que el smoke no dejó la sesión en estado inválido** *(15 min)*
  - Después del caso 2 (409), ejecutar el caso 1 con un `nombre` distinto → debe responder **201** (la sesión se recuperó con `rollback()`).
  - **Verificación**: el alta posterior al 409 se completa con **201**, sin error de sesión.

## Workflow follow-up

- Archivar el change con `/opsx:archive practicas-catalogo` y marcar `[x]` en `CHANGES.md` (solo la línea `[04]`) una vez revisado.
- Avisar al dueño de [06] `turnos-alta-transaccional` que el catálogo ya está disponible: `GET /practicas/` y `POST /practicas/` funcionan y el precio se serializa como string.