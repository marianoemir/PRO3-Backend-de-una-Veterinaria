# Diseño: mascotas-y-paginacion

## Context

Ver `proposal.md` §Why. El estado de partida que condiciona el diseño:

- `app/modules/mascotas/models.py` ya está completo (change [02]): `Mascota` (`id` PK autoincremental, `nombre`, `especie`, `duenio_id` FK `ON DELETE RESTRICT` con índice) y la relación `duenio` a uno. **No se toca.**
- `app/modules/mascotas/{schemas,service,router}.py` son stubs vacíos (`router.py` solo declara `router = APIRouter()`); `app/main.py` ya incluye el router de `mascotas` (change [01]), así que no se edita.
- `app/modules/duenios/*` está implementado y archivado ([03]) y sirve de referencia de estilo: DTOs Pydantic separados de los modelos, `service` que recibe la `AsyncSession` (DD-02), `IntegrityError` → `rollback()` → 409, español y type hints.
- `app/core/database.py` expone `get_session` (una `AsyncSession` por petición, `expire_on_commit=False`, RN-21) y el motor se crea con `echo=True`, lo que permite contar consultas en la consola de `uvicorn`.
- El seed de `reiniciar.py` ([09]) deja 3 mascotas: `1` = Toby (perro, dueño 1), `2` = Michi (gato, dueño 1), `3` = Rocco (perro, dueño 2); dueño 1 = Ana Gómez, dueño 2 = Bruno Díaz.
- El entorno de verificación es `uvicorn app.main:app` + peticiones HTTP (curl o `.http`) y consultas en pgAdmin (sin `psql`).

## Goals / Non-Goals

**Goals (nivel diseño)**

- Que el alta de mascota deje la pertenencia al dueño en manos de la FK `mascota.duenio_id`: se escribe y, si el dueño no existe, se captura `IntegrityError`, se hace `rollback()` y se responde 409, sin `SELECT` previo de existencia.
- Que el detalle y el listado devuelvan el dueño resumido **sin carga perezosa** y con un número de consultas que no dependa de la cantidad de filas: una consulta en el detalle, dos fijas en el listado.
- Que el envoltorio de paginación cumpla RN-13 al pie de la letra: `size` 20 por defecto y 1..100, página fuera de `pages` → 422, primera página siempre 200 incluso con la base vacía (`pages: 0`).
- Que los tres endpoints usen `async def`, `Depends(get_session)` y no contengan lógica de negocio.

**Non-Goals**

- No se agrega `DELETE /mascotas/{id}`, `PATCH /mascotas/{id}` ni ningún otro endpoint no listado en `knowledge-base/02_descripcion_general.md` (IN-02, regla dura 10).
- No se agrega búsqueda, filtros por dueño/especie, orden configurable ni paginación al listado de `duenios` (DD-10).
- No se agrega unicidad de `nombre` ni de `(duenio_id, nombre)`: la consigna no la enuncia y el esquema no la tiene.
- No se toca `models.py`, `app/modules/duenios/*`, `app/main.py`, `reiniciar.py`, `test/**` ni `README.md`.
- No se crean DTO compartidos ni se importan DTO de `duenios` (RN-10 y regla de CHANGES.md).

## Decisions

### 1. DTOs del módulo y vista resumida propia del dueño (RN-10)

`mascotas/schemas.py` define todos los DTO del módulo con Pydantic, separados de los modelos de tabla:

- **`MascotaCreate`**: `nombre: str`, `especie: str`, `duenio_id: int`. **Sin `id`** (RN-10). `especie` es texto libre no vacío (`min_length=1`, DD-12).
- **`DuenioResumenRead`**: `id: int`, `nombre: str`, con `ConfigDict(from_attributes=True)`. Es la vista resumida **propia de este módulo**; no expone `email` ni la ficha.
- **`MascotaRead`**: `id`, `nombre`, `especie`, `duenio: DuenioResumenRead`, con `from_attributes=True`.
- **`PaginaMascotasRead`**: `items: list[MascotaRead]`, `total: int`, `page: int`, `size: int`, `pages: int`. Los nombres y el orden de las claves son los del envoltorio de `knowledge-base/02_descripcion_general.md` §Envoltorio de paginación (RN-13).

**Por qué la vista propia y no `DuenioRead` de `duenios`**: CHANGES.md §Reglas de trabajo prohíbe que un módulo importe DTO de otro, y RN-10 pide los DTO por módulo. Además `DuenioRead` arrastra `email` y `ficha`, datos que US-010 no necesita: el detalle de mascota solo tiene que responder "a quién pertenece". Se replica la forma de "vista resumida" que ya usan `duenios` (`MascotaResumenRead` con `id`, `nombre`, `especie`) y `turnos` (`mascota` resumida).

**Alternativas descartadas**: importar `DuenioRead` (acopla módulos y filtra datos de contacto); devolver solo `duenio_id` (obliga al cliente a una segunda petición y no cumple US-010, que pide ver el dueño junto con la mascota).

### 2. Alta: escribir y capturar el `IntegrityError` de la FK (RN-12, DD-03, IN-05)

`crear_mascota` construye `Mascota(nombre=..., especie=..., duenio_id=dto.duenio_id)`, hace `session.add()` + `await session.commit()` y **no consulta** si el dueño existe. Si la FK rechaza el `INSERT`, captura `sqlalchemy.exc.IntegrityError`, ejecuta `await session.rollback()` y lanza `HTTPException(status_code=409, detail="No existe un dueño con ese id")`.

- **Por qué 409 y no 422**: 422 es la validación de contrato (cuerpo o parámetros mal formados, RN-12) y la hace FastAPI antes del handler; un `duenio_id` entero y bien tipado **cumple** el contrato aunque apunte a un dueño que no existe. Lo que falla es la escritura, y RN-12 reserva **409** para "la base rechaza la escritura". La tabla de endpoints declara `201, 409, 422` para `POST /mascotas/` e IN-05 confirma que el único conflicto identificable es la FK.
- **Por qué 409 y no 404**: el recurso direccionado por la petición es la colección `/mascotas/`, que existe; el dueño ausente es una referencia del cuerpo, no la ruta. Devolver 404 confundiría "ruta inexistente" con "referencia inválida", y la tabla no lista 404 para este endpoint.
- **Por qué sin `SELECT` previo**: entre el `SELECT` de control y el `INSERT` hay una ventana de carrera (consigna §4.10, DD-03); la única garantía atómica es la FK. Además evita una consulta por alta.
- **`rollback()` en el mismo `except`**: sin él la sesión queda en "pending rollback" y la petición siguiente falla. Se verifica encadenando un 409 con un alta válida.

**Alternativas descartadas**: `select(Duenio.id)` antes del `INSERT` (prohibido por la regla dura 3 y por DD-03); capturar solo el nombre de la restricción para distinguir FK de otras violaciones (acopla el service al nombre que PostgreSQL genera y no aporta nada aquí).

### 3. La respuesta del alta se arma con una lectura explícita, no con carga perezosa (RN-14, RN-16)

Después del `commit()`, el service ejecuta una segunda sentencia:

```python
resultado = await session.execute(
    select(Mascota)
    .options(joinedload(Mascota.duenio))
    .where(Mascota.id == mascota.id)
    .execution_options(populate_existing=True)
)
return resultado.scalars().one()
```

`populate_existing=True` es necesario porque la instancia recién insertada ya está en el identity map: fuerza a que el `JOIN` refresque el estado y deje `Mascota.duenio` poblado. Así la respuesta 201 incluye `duenio: {id, nombre}` sin ninguna carga perezosa.

- **Por qué no serializar el objeto recién creado**: `Mascota.duenio` no está cargada; al serializar `MascotaRead` con `from_attributes`, SQLAlchemy intentaría una carga perezosa y en asíncrono fallaría con `MissingGreenlet` (RN-16).
- **Costo**: 2 sentencias fijas por alta (`INSERT` + `SELECT` de lectura), independientes del contenido.
- **Coherencia con [06]**: el alta de turno ya resuelve su respuesta con una re-consulta con carga anticipada; se aplica el mismo patrón.

**Alternativas descartadas**: `await session.refresh(mascota, ["duenio"])` (emite su propio `SELECT` sin `JOIN` declarado: mismo costo, carga implícita y no expresa la precarga); devolver `duenio` incompleto o `null` (rompe US-010 y el contrato del DTO); `SELECT` del dueño antes del `INSERT` (prohibido, decisión 2).

### 4. Detalle con carga anticipada en una sola consulta (RN-14, RN-15)

`obtener_mascota` ejecuta:

```python
select(Mascota).options(joinedload(Mascota.duenio)).where(Mascota.id == mascota_id)
```

y devuelve `None` si no hay fila; el router responde **404** con mensaje propio. Es **un** `SELECT` con `JOIN` a `duenio` (`joinedload` emite `LEFT OUTER JOIN` por defecto; la FK es `NOT NULL`, así que el resultado es una fila por mascota), igual para cualquier mascota: la cantidad de consultas no depende de datos. No se toca `Mascota.turnos`, que el DTO no expone.

**Alternativa descartada**: dos consultas (mascota y luego dueño). Duplica viajes sin beneficio frente a un `joinedload` de relación "a uno" (DD-04).

### 5. Listado: `count(*)` + página, dos consultas fijas (RN-13, RN-15, DD-15)

`listar_mascotas(session, page, size)`:

1. `total = (await session.execute(select(func.count()).select_from(Mascota))).scalar_one()`.
2. `pages = math.ceil(total / size) if total else 0`.
3. Si `page > 1 and page > pages` → `HTTPException(422, "La página solicitada no existe")`.
4. `select(Mascota).options(joinedload(Mascota.duenio)).order_by(Mascota.id).offset((page - 1) * size).limit(size)`.

Ventajas verificables:

- **Dos consultas fijas**: el `count(*)` ya es necesario para `total`, y de él sale `pages`; la validación de rango **no** agrega una tercera consulta. La página se resuelve con `offset`/`limit` y un solo `JOIN` para el dueño, así que el número de sentencias no crece con la cantidad de mascotas ni con el tamaño de la página (RN-15, y el mismo criterio de RN-14 para no caer en N+1 al serializar el dueño de cada item).
- **`items` con `MascotaRead`**: el listado devuelve la misma forma que el detalle y el alta; el dueño se precarga una vez para toda la página, no una vez por mascota.
- **Orden por `id` ascendente**: DD-15.
- **Complejidad**: `count(*)` recorre la tabla (O(n) con scan secuencial, O(log n + size) con scan de índice si PostgreSQL lo elige); el `offset`/`limit` con `ORDER BY id` usa el índice de la PK. Memoria O(size). Para el volumen del TP es irrelevante.

**Alternativas descartadas**: `len(items)` como `total` (solo vale si se traen todas las filas: contradice el objetivo de paginar); `selectinload(Mascota.duenio)` (para una relación "a uno" `joinedload` resuelve en la misma consulta; `selectinload` agregaría una sentencia, ver DD-04); una consulta previa de existencia de página con `LIMIT 1 OFFSET n` (tercera consulta para lo mismo que ya dice `total`).

### 6. Página fuera de rango: 422, con la primera página como excepción (RN-13)

`pages` es `ceil(total / size)` y vale `0` cuando no hay filas, como en el ejemplo del envoltorio (`"pages": 0`). La validación es `page > 1 and page > pages`:

- **Página más allá de `pages`** (por ejemplo `?page=99&size=20` con `pages = 1`) → **422**, tal como enuncia RN-13. Devolver 200 con `items: []` sería inventar un comportamiento que la regla niega.
- **Primera página siempre 200**: con `total = 0` se cumple `pages = 0`, pero `page = 1` no entra en la condición, así que responde 200 con `items: []`, `total: 0`, `pages: 0`. La excepción es literal de RN-13 ("la primera página siempre responde aunque no haya resultados") y evita el absurdo de que una base vacía no se pueda listar.
- **`page` 1-based**: el ejemplo del envoltorio trae `"page": 1` y la consigna habla de "la primera página". Se declara `page: int = Query(1, ge=1)`: `page = 0` o negativo no cumple el contrato → **422** antes del handler (RN-12). Sin ese límite, `offset = (page - 1) * size` sería negativo y PostgreSQL rechazaría la sentencia con un 500, que no es un código del contrato.

**Decisión propia registrada**: el carácter 1-based de `page` no está enunciado como regla; se deriva del ejemplo y de RN-13. Se documenta en el `design.md` y debe mencionarse en el README como decisión del equipo, igual que DD-08 a DD-15. Si la cátedra esperara base 0, el cambio se limita al `Query(..., ge=0)` y a la fórmula del `offset`.

**Alternativa descartada**: normalizar `page=0` a la primera página en silencio. Oculta un error del cliente y agrega un comportamiento que nadie pidió.

### 7. `size` acotado por el contrato del parámetro (RN-13)

`size: int = Query(20, ge=1, le=100)`: FastAPI/Pydantic responden **422** para `size=0`, `size=101` o valores no enteros, sin ejecutar ninguna consulta sobre `mascota`. El valor por defecto 20 y el rango 1..100 son exactamente los de RN-13 y el ejemplo del envoltorio; no se agrega ninguna otra cota.

**Alternativa descartada**: validar el rango dentro del service con un `if` y `HTTPException(422)`. Funciona igual, pero duplica en el service un contrato que FastAPI ya expresa en la firma del handler y que se refleja en `/openapi.json`.

### 8. Router: prefijo, barra final y handlers asíncronos (SU-05, RN-17, RN-21)

`APIRouter(prefix="/mascotas", tags=["mascotas"])` con:

- `@router.post("/", response_model=MascotaRead, status_code=201)`
- `@router.get("/", response_model=PaginaMascotasRead)`
- `@router.get("/{mascota_id}", response_model=MascotaRead)`

La colección conserva la barra final que muestra la tabla de endpoints (SU-05: `/mascotas/`) y el detalle no la lleva. Todos los handlers son `async def`, reciben `session: AsyncSession = Depends(get_session)` y delegan en el service; el router no valida reglas de negocio (DD-02). `page` y `size` se declaran `Query(...)` y `mascota_id: int`, de modo que un id no entero responde 422 por validación de ruta (RN-12), igual que en `duenios`.

### 9. Imports del service: registrar los mappers, no usarlos

`mascotas/service.py` arranca con:

```python
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

import app.modules.duenios.models  # noqa: F401
import app.modules.mascotas.models  # noqa: F401
import app.modules.turnos.models  # noqa: F401

from app.modules.mascotas.models import Mascota
```

- `import app.modules.duenios.models  # noqa: F401` es **obligatorio**: `Mascota.duenio` se declara con el string `"Duenio"` y, si el mapper de `Duenio` no está registrado, la configuración falla con `InvalidRequestError`.
- `import app.modules.turnos.models  # noqa: F401` es **obligatorio** por la misma razón: `Mascota.turnos` apunta a `"Turno"`. Es el mismo bloque que ya usa `duenios/service.py`.
- Los `noqa: F401` documentan que esos imports son para registrar mappers, no para usar los nombres.

### 10. Códigos HTTP: quién produce cada uno (RN-12)

- **201**: alta exitosa.
- **200**: detalle y listado (incluida la primera página vacía).
- **404**: el service devuelve `None`/no encuentra la mascota en el detalle.
- **409**: el service captura `IntegrityError` en el alta (FK a un dueño inexistente). Es el único conflicto posible: `mascota` no tiene `UNIQUE` ni `CHECK`.
- **422**: FastAPI/Pydantic antes del handler — cuerpo inválido (`MascotaCreate`), `size` fuera de 1..100, `page < 1`, `mascota_id` no entero — y el service cuando la página pedida supera `pages`.

### 11. Consultas esperadas por operación

| Operación | Sentencias fijas | Detalle |
|---|---|---|
| `POST /mascotas/` | **2** | `INSERT` + `SELECT` con `JOIN` para armar la respuesta (decisión 3) |
| `GET /mascotas/{id}` | **1** | `SELECT` con `JOIN` a `duenio` |
| `GET /mascotas/` | **2** | `COUNT` + `SELECT` de la página con `JOIN` a `duenio` |

Ninguna de las tres depende de la cantidad de filas: no hay N+1 y no hay carga perezosa (RN-14, RN-15, RN-16).

## Risks / Trade-offs

- [`IntegrityError` genérico traducido a 409 aunque la violación sea otra] → En `mascota` la única restricción alcanzable por este endpoint es la FK y el `NOT NULL` (que el DTO ya impide); responder 409 es coherente con "la base rechaza la escritura" y el mensaje propio nombra el conflicto esperado. Aceptado y documentado.
- [Serializar `Mascota.duenio` en el alta dispara carga perezosa y `MissingGreenlet`] → Se resuelve con la re-lectura con `joinedload` + `populate_existing` (decisión 3); el smoke verifica que `POST /mascotas/` responde 201 con el dueño.
- [`pages` con off-by-one y la base vacía] → La condición `page > 1 and page > pages` cubre el caso `total = 0`; se verifica con un escenario explícito de base vacía y con `page=99`.
- [El `count(*)` recorre la tabla] → Costo aceptable para el volumen del TP; es la única forma de calcular `total` y `pages` sin traer todas las filas. `mascota` es pequeña y `ORDER BY id` usa el índice de la PK.
- [Concurrencia entre `count(*)` y la consulta de página] → Si otra petición inserta o borra entre ambas, la página puede quedar vacía aunque `total` diga que existía. La consigna no exige una foto consistente y una transacción `REPEATABLE READ` sería desproporcionada. Aceptado.
- [Un `IntegrityError` sin `rollback()` deja la sesión inutilizable] → El `rollback()` está en el mismo `except`, antes de lanzar la excepción; el smoke encadena un 409 con un alta válida.
- [El listado devuelve el dueño en cada item] → Es la forma consistente con `MascotaRead`; se precarga una sola vez por página con `joinedload`, así que no cuesta una consulta por item (decisión 5).

## Plan de migración / rollback

- No hay migraciones (DD-01). El esquema ya existe (change [02]); este change solo agrega código.
- **Aplicación**: completar `schemas.py`, `service.py` y `router.py`; correr `python reiniciar.py` ([09]) y levantar `uvicorn app.main:app` para ejecutar el smoke del change.
- **Rollback**: vaciar los tres archivos a stubs (`router = APIRouter()`). Sin impacto en la base ni en otros módulos: ningún módulo importa DTO de `mascotas` y el router ya estaba registrado en `app/main.py` desde [01].

## UI Mockups

Decision: no (no UI)

Este change es exclusivamente backend: no agrega pantallas, componentes, estilos ni interacciones. No se crean mockups ni se aplica la compuerta visual.

## Preguntas abiertas

- ¿La cátedra espera `page` con base 0? La consigna no lo dice; se adoptó **base 1** por el ejemplo del envoltorio (`"page": 1`) y para no generar `offset` negativos. Es una decisión propia: si se confirmara base 0, cambia solo la cota del `Query` y la fórmula del `offset`, no el resto del diseño. No bloquea la implementación.
- El resto de los puntos que la consigna deja abiertos y tocan a `mascotas` ya están resueltos como decisión propia en la KB: `especie` como texto libre no vacío (DD-12), `page`/`size` como query params y orden por `id` (DD-15), 409 únicamente por violación de FK (IN-05) y envoltorio de paginación exclusivo de `GET /mascotas/` (DD-10).
