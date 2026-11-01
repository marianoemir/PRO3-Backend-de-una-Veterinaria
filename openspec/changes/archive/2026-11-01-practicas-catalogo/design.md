# Diseño: practicas-catalogo

## Contexto

Ver `proposal.md` §Why. El estado de partida que condiciona el diseño:

- `app/modules/practicas/models.py` ya está completo (change [02]): tabla `practica` con `id` PK autoincremental, `nombre` `UNIQUE`, `precio` `NUMERIC(10,2)` con `CHECK (precio > 0)`, y la relación `Practica.turnos` hacia `TurnoPractica`. **No se toca** (propiedad de [02], DD-03).
- `app/modules/practicas/{schemas,service,router}.py` son stubs vacíos; `app/main.py` ya registra el router de `practicas` (change [01]), así que no se edita.
- `app/core/database.py` expone `get_session` (async generator que entrega `AsyncSession` con `expire_on_commit=False`), y `app.state.session_local` es la fábrica.
- La corrección revisa los códigos HTTP (201/409/422/200), la serialización del precio como string y la ausencia de `SELECT` previo. El entorno de verificación es pgAdmin + archivos `.http` (sin `psql`).
- SQLModel 0.0.48 + Pydantic 2.x: `Field(gt=0)` funciona sobre `Decimal` y `field_serializer` controla la serialización JSON.

## Goals / Non-Goals

**Goals (nivel diseño)**

- Que `POST /practicas/` valide el precio en el DTO (422 si `<= 0`) y delegue la unicidad del nombre a la base (409 por `IntegrityError`), sin `SELECT` previo.
- Que `GET /practicas/` devuelva el catálogo en una sola consulta ordenada por `id`.
- Que `PracticaRead.precio` salga como **string decimal** con dos decimales (`"15000.00"`), nunca como número ni `float`.
- Que el service no deje la sesión en estado inválido tras un `IntegrityError` (rollback obligatorio).

**Non-Goals**

- No se agregan `PATCH`, `DELETE` ni `GET /practicas/{id}`: la consigna no los lista (IN-02). El catálogo solo se consume por alta y listado.
- No se normaliza ni valida el formato del `nombre` (mayúsculas, longitud): DD-12 (validaciones mínimas).
- No se toca `models.py`, `app/main.py`, ni se crean tests (eso es [10]).
- No se implementa paginación en el listado: la consigna solo pagina mascotas (RN-13).

## Decisiones

### 1. DTOs separados del modelo (RN-10)

`PracticaCreate` y `PracticaRead` viven en `schemas.py` y no exponen el modelo `Practica` directamente.

- **`PracticaCreate`**: `nombre: str` (obligatorio, no vacío por defecto de Pydantic) y `precio: Decimal = Field(gt=0)`. **Sin `id`**. El `gt=0` cubre RN-04 en el DTO: `precio = 0` y `precio < 0` fallan la validación de Pydantic → FastAPI responde **422** automáticamente, antes de llegar al service. No se hace `SELECT` ni se consulta la base.
- **`PracticaRead`**: `id: int`, `nombre: str`, `precio: Decimal` con un `@field_serializer("precio")` que devuelve `f"{v:.2f}"` (string). Así el JSON sale `"precio": "15000.00"` (DD-06), nunca un número.

**Alternativa descartada**: declarar `precio: str` en `PracticaRead` y convertir en el service. Rompe la tipificación (el campo deja de ser `Decimal`) y obliga a casteos manuales en [06] cuando se copie el precio al turno. Mantener `Decimal` en el DTO y serializar con `field_serializer` conserva el tipo en Python y solo cambia la representación JSON.

### 2. Unicidad por la base, no por consulta previa (RN-02, DD-03)

`crear_practica` hace `session.add(practica)` + `await session.commit()` directo. Si la base rechaza el `INSERT` por la restricción `UNIQUE` de `practica.nombre`, se captura `sqlalchemy.exc.IntegrityError`, se ejecuta `await session.rollback()` y se lanza `HTTPException(status_code=409, detail="Ya existe una práctica con ese nombre")`.

- **No hay `SELECT` previo** para "ver si existe": entre la pregunta y el `INSERT` hay una ventana de carrera; la única garantía atómica es la restricción de la base (sección 4.10 de la cátedra).
- Tras el `IntegrityError`, el `rollback()` deja la sesión limpia para la siguiente petición; sin él, la sesión queda en estado "pending rollback" y falla la próxima operación.
- `await session.refresh(practica)` después del `commit` asegura que `id` y los defaults vengan de la base (con `expire_on_commit=False` los atributos ya están, pero el `refresh` es defensivo y barato).

**Alternativa descartada**: verificar con `SELECT ... WHERE nombre = ?` antes de insertar. Viola la regla dura del proyecto y reintroduce la carrera. Descartada por RN-02 y DD-03.

### 3. Distinguir 422 (DTO) de 409 (base)

- **422**: lo produce FastAPI/Pydantic al validar `PracticaCreate` (`precio <= 0`, falta de campo, tipo incorrecto). El service **no se ejecuta**.
- **409**: lo produce el service al capturar `IntegrityError` del `INSERT` (nombre repetido). El `CHECK (precio > 0)` de la base **no se ejercita en el flujo normal** porque el DTO ya lo bloquea; si algún día se violara (p. ej. un cliente que salte el DTO), la base respondería con otro `IntegrityError` que este service clasificaría como 409 — comportamiento aceptable y coherente con la regla "IntegrityError → 409" del proyecto. No se distingue por nombre de restricción para no acoplar el service al esquema.

### 4. Listado en una sola consulta (DD-15, RN-15)

`listar_practicas` ejecuta `SELECT practica ORDER BY id` y devuelve `list(result.scalars().all())`. Una sola consulta, número fijo, sin N+1 (no hay relaciones que cargar: `PracticaRead` solo tiene campos escalares). El orden por `id` ascendente es DD-15 y es el que espera el smoke ("el listado devuelve las prácticas").

**Alternativa descartada**: cargar `Practica.turnos` con `selectinload`. Innecesario para este change (no se expone en `PracticaRead`) y añadiría una consulta extra. Se deja para [06] si hiciera falta.

### 5. Router con `prefix="/practicas"` y barra final (SU-05)

`APIRouter(prefix="/practicas", tags=["practicas"])` con rutas `@router.post("/")` y `@router.get("/")`, de modo que las rutas efectivas sean `/practicas/` (con barra final), tal como las muestra la tabla de endpoints de la consigna. Se declaran `response_model=PracticaRead` (alta) y `response_model=list[PracticaRead]` (listado), y `status_code=201` en el POST. Todos los handlers son `async def` (RN-17). La sesión llega por `Depends(get_session)` (RN-21).

### 6. Serialización del precio: `field_serializer` (DD-06)

Pydantic v2 serializa `Decimal` como número por defecto, lo que rompería el requisito de string. Se usa:

```python
@field_serializer("precio")
def _serialize_precio(self, v: Decimal) -> str:
    return f"{v:.2f}"
```

Garantiza dos decimales y evita notación científica. El formato `f"{v:.2f}"` aplica redondeo a 2 decimales, coherente con `NUMERIC(10,2)`.

## Risks / Trade-offs

- [Riesgo] `IntegrityError` genérico capturado como 409 aunque la violación sea otra (p. ej. un `CHECK`). → Mitigación: el DTO bloquea `precio <= 0` antes; el flujo normal solo puede violar la `UNIQUE` de `nombre`. Si se violara el `CHECK`, responder 409 es conservador y no rompe el smoke (que usa el DTO). Aceptado.
- [Riesgo] `session.rollback()` olvidado tras `IntegrityError` deja la sesión en estado inválido. → Mitigación: el `rollback()` está en el mismo bloque `except`, antes de lanzar la excepción. Verificado en el smoke (alta duplicada seguida de un alta válida).
- [Riesgo] `field_serializer` no se aplica si el modelo se serializa con `model_dump()` en lugar de `model_dump_json()`. → Mitigación: FastAPI usa `model_dump_json()` por defecto para `response_model`; el smoke verifica el JSON real. Si un consumidor futuro usa `model_dump()`, el precio saldrá como `Decimal` (no string) — documentado.
- [Riesgo] `PracticaCreate.nombre` vacío (`""`) se acepta. → Mitigación: la consigna no exige validación de nombre no vacío (DD-12); se acepta para no inventar reglas. Si la cátedra exigiera no vacío, se añade `min_length=1` en el DTO.
- [Trade-off] El service lanza `HTTPException` directamente. Acopla el service a FastAPI, pero es el patrón del proyecto (la KB dice que el service traduce `IntegrityError` → 409) y evita una capa extra de excepciones de dominio que el TP no pide (DD-02, sin repositorios).

## Plan de migración / rollback

- No hay migraciones (DD-01). El esquema ya existe (change [02]); este change solo agrega código.
- **Aplicación**: completar los tres archivos; levantar `uvicorn app.main:app`; ejecutar el smoke (alta válida, duplicado 409, precio 0/negativo 422, listado con precio como string).
- **Rollback**: vaciar los tres archivos a stubs (router = `APIRouter()`). Sin impacto en la base ni en otros módulos (ningún importa DTO de `practicas`).

## Preguntas abiertas

Ninguna que afecte este change. Los puntos que la consigna deja abiertos y que tocan a `practicas` (validación mínima de `nombre`, normalización de email no aplica) están resueltos por DD-12 y registrados arriba. Si la cátedra exigiera `min_length` en `nombre`, el cambio se limita al DTO.