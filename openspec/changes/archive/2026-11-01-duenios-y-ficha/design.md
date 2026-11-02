# Diseño: duenios-y-ficha

## Contexto

Ver `proposal.md` §Why. El estado de partida que condiciona el diseño:

- `app/modules/duenios/models.py` ya está completo (change [02]): `Duenio` (`id` PK, `nombre`, `email` `UNIQUE`) con `ficha` a uno (`uselist=False`) y `mascotas` como colección; `FichaDuenio` (`id` PK, `duenio_id` FK `UNIQUE` sin `ON DELETE`, `telefono`, `direccion`). **No se toca** (propiedad de [02]).
- `app/modules/mascotas/models.py` ya está completo (change [02]): `Mascota` (`id`, `nombre`, `especie`, `duenio_id` FK `ON DELETE RESTRICT` con índice). **No se toca.**
- `app/modules/duenios/{schemas,service,router}.py` son stubs vacíos; `app/main.py` ya registra el router de `duenios` (change [01]), así que no se edita.
- `app/core/database.py` expone `get_session` (una `AsyncSession` por petición, `expire_on_commit=False`); `echo=True` está activo en el motor, lo que permite verificar el número de consultas.
- SQLModel 0.0.48 + Pydantic 2.x: `model_dump(exclude_unset=True)`, `ConfigDict(from_attributes=True)` y `Field` sobre tipos opcionales.
- El entorno de verificación es `uvicorn` + peticiones HTTP (`.http` o curl) y pgAdmin (sin `psql`).

## Goals / Non-Goals

**Goals (nivel diseño)**

- Que las tres garantías del dominio dueños las haga cumplir PostgreSQL: `UNIQUE (duenio.email)` → 409, `UNIQUE (ficha_duenio.duenio_id)` → 409 y `mascota.duenio_id ON DELETE RESTRICT` → 409, siempre escribiendo y capturando `IntegrityError`, con `rollback()` y sin `SELECT` previo de existencia.
- Que `GET /duenios/{id}` resuelva dueño + ficha en **una** consulta con `joinedload`, y que ninguna respuesta dependa de carga perezosa en contexto asíncrono.
- Que `PATCH` aplique solo los campos enviados (`exclude_unset`) y que un cuerpo vacío no borre nada.
- Que la baja deje la decisión de borrado **exclusivamente** a la base, sin que el ORM anule claves foráneas hijas.
- Que `GET /duenios/{id}/mascotas` devuelva una lista simple ordenada por `id`, con una vista de mascota definida en este módulo.

**Non-Goals**

- No se agrega `GET /duenios/` (IN-01) ni `DELETE`/`PATCH` de ficha (IN-02): no están en la tabla de endpoints.
- No se agrega paginación a `GET /duenios/{id}/mascotas` (DD-10).
- No se normaliza el email ni se valida su formato (DD-09, DD-12); no se valida el formato de `telefono` ni de `direccion` (DD-12).
- No se toca `models.py`, `app/main.py`, `reiniciar.py`, `test/**` ni `README.md`.
- No se crean DTO compartidos entre módulos: la vista de mascota de este change vive en `duenios/schemas.py` (RN-10).

## Decisions

### 1. DTOs del módulo y vista propia de mascota (RN-10)

`duenios/schemas.py` define todos los DTO del módulo con Pydantic, separados de los modelos de tabla:

- **`DuenioCreate`**: `nombre: str`, `email: str`. **Sin `id`**. Pydantic ignora campos extra por defecto, así que un `id` enviado por el cliente no se usa (la base genera el suyo).
- **`DuenioUpdate`**: `nombre: str | None = None`, `email: str | None = None` (DD-08). Ambos opcionales; `id` no se modifica.
- **`DuenioRead`**: `id`, `nombre`, `email`, `ficha: FichaRead | None`, con `model_config = ConfigDict(from_attributes=True)`.
- **`FichaCreate`**: `telefono: str`, `direccion: str` (obligatorios, DD-12).
- **`FichaRead`**: `id`, `duenio_id`, `telefono`, `direccion` (`from_attributes=True`).
- **`MascotaResumenRead`**: `id`, `nombre`, `especie` (`from_attributes=True`). Es la **vista resumida propia de este módulo** para `GET /duenios/{id}/mascotas`; replica la forma de "mascota resumida" del resto de la API sin importar `MascotaRead` de `mascotas`.

**Alternativa descartada**: importar `MascotaRead` desde `app.modules.mascotas.schemas`. Viola la regla del proyecto "ningún módulo importa DTO de otro" (CHANGES.md §Reglas de trabajo) y acopla este change a [05], que todavía no existe.

### 2. Unicidad de email: escribir y capturar el `IntegrityError` (RN-01, DD-03)

`crear_duenio` construye `Duenio(nombre=..., email=...)`, hace `session.add()` + `await session.commit()` y **no consulta** si el email existe. Si el `INSERT` viola `UNIQUE (duenio.email)`, captura `sqlalchemy.exc.IntegrityError`, ejecuta `await session.rollback()` y lanza `HTTPException(status_code=409, detail="Ya existe un dueño con ese email")`.

- La restricción de la base es la única garantía atómica: entre un `SELECT` de control y el `INSERT` hay una ventana de carrera (consigna §4.10).
- El `rollback()` en el mismo `except` deja la sesión limpia; sin él la sesión queda en "pending rollback" y la petición siguiente falla. Se verifica en el smoke encadenando un 409 con un alta válida.
- **Sin `refresh`**: `expire_on_commit=False` conserva los valores y la PK ya está poblada tras el `commit`. Un `refresh` sería una consulta extra innecesaria.

### 3. El alta no toca la relación `ficha` (evita `MissingGreenlet`)

`POST /duenios/` responde con un `DuenioRead` construido **explícitamente** con `ficha=None`, en lugar de devolver el objeto `Duenio` para que `from_attributes` lo serialice.

- Un `Duenio` recién creado no tiene la relación `ficha` cargada; si la serialización la consultara, SQLAlchemy intentaría una carga perezosa y en asíncrono fallaría con `MissingGreenlet` (RN-16).
- Un dueño recién creado no puede tener ficha (la ficha se crea en otro endpoint), así que `None` es el valor correcto y verificable.

**Alternativa descartada**: `await session.refresh(duenio, ["ficha"])` después del `commit`. Agrega una consulta y hace que el alta dependa de la relación solo para devolver `null`.

### 4. Detalle con carga anticipada en una sola consulta (RN-14, RN-15)

`obtener_duenio` ejecuta:

```python
select(Duenio).options(joinedload(Duenio.ficha)).where(Duenio.id == duenio_id)
```

y devuelve `None` si no hay fila (el router responde 404). Es **un** `SELECT` con `LEFT OUTER JOIN` a `ficha_duenio`, igual para un dueño con ficha y para uno sin ficha: el número de consultas no depende de si la ficha existe (RN-15). No se toca `Duenio.mascotas`, que no se expone en el detalle.

**Alternativa descartada**: dos consultas (dueño y luego ficha). Duplica viajes y no aporta nada frente a un `joinedload` de relación "a uno".

### 5. `PATCH` parcial con `exclude_unset` (RN-11, DD-08)

`actualizar_duenio` carga el dueño con `joinedload(Duenio.ficha)` —la misma consulta del detalle, para responder 404 y para tener la ficha precargada— y aplica:

```python
for campo, valor in dto.model_dump(exclude_unset=True).items():
    setattr(duenio, campo, valor)
```

Luego `commit()`. Consecuencias verificables:

- Un cuerpo `{}` produce un diccionario vacío: no se modifica ninguna columna y la respuesta es 200 con el dueño intacto.
- Un cuerpo con solo `nombre` no toca `email`, porque `exclude_unset` distingue "no enviado" de "enviado con el mismo valor".
- Un email que colisiona viola `UNIQUE` → `rollback()` → 409 con el mensaje exacto `"No se pudo actualizar: email ya registrado o dato inválido"`, y el email original queda intacto. Es un mensaje genérico propio del `PATCH` porque la misma rama cubre también el rechazo de la base por un `null` explícito; el alta y la ficha conservan sus mensajes propios.
- Se devuelve el mismo objeto cargado (la ficha sigue precargada y `expire_on_commit=False` conserva el estado): 2 sentencias fijas (`SELECT` + `UPDATE`), sin `SELECT` posterior.
- **Caso borde documentado**: enviar `{"nombre": null}` o `{"email": null}` de forma explícita aplica `None` y la base rechaza el `NOT NULL` con `IntegrityError` → 409. No se agrega una validación de "no nulo" en el DTO porque la consigna no la enuncia (DD-12); se acepta el 409 como traducción del rechazo de la base.

**Alternativa descartada**: construir el `UPDATE` solo con las claves presentes usando SQL Core. Repite la lógica del ORM y complica la respuesta con ficha precargada; `exclude_unset` es exactamente lo que pide RN-11.

### 6. Baja con `DELETE` de Core para que decida la base (RN-08, DD-05, DD-13)

`borrar_duenio` **no** usa `session.delete(duenio)`. El `try` envuelve **todo** el bloque —el `DELETE`, el chequeo de `rowcount` y el `commit()`—:

```python
try:
    resultado = await session.execute(
        delete(Duenio).where(Duenio.id == duenio_id).execution_options(synchronize_session=False)
    )
    if resultado.rowcount == 0:
        raise HTTPException(status_code=404, ...)
    await session.commit()
except IntegrityError:
    await session.rollback()
    raise HTTPException(status_code=409, ...)
```

- **Por qué el `try` empieza en el `execute` y no en el `commit`**: `ON DELETE RESTRICT` (mascotas) y `NO ACTION` (ficha) se evalúan al **ejecutar** el `DELETE`, no al confirmar. PostgreSQL rechaza la sentencia en el `execute`, así que un `try` que empiece en el `commit()` deja escapar el `IntegrityError` sin `rollback()` y la sesión queda en "pending rollback". Con el `try` desde el `execute`, cualquier rechazo de la base pasa por el mismo `except`.
- **El 404 no queda enmascarado**: el `HTTPException` se lanza dentro del `try`, pero `HTTPException` no es `IntegrityError`, así que el `except` no lo captura y propaga normal como 404.
- **Por qué no `session.delete`**: al borrar un padre, el ORM recorre las relaciones sin `passive_deletes` y, para una relación uno-a-muchos, intenta **anular** la FK de los hijos (`UPDATE mascota SET duenio_id = NULL ...` / `UPDATE ficha_duenio SET duenio_id = NULL ...`). Como ambas columnas son `NOT NULL`, el `flush` fallaría por `NOT NULL` en lugar de por `RESTRICT`/`NO ACTION`, y además emitiría consultas y `UPDATE` que la consigna no pide. El `DELETE` de Core no sincroniza relaciones: emite una sola sentencia y deja que PostgreSQL aplique `ON DELETE RESTRICT` (mascotas) o `NO ACTION` (ficha).
- **404 sin `SELECT` previo**: `rowcount == 0` indica que no había fila. Es una comprobación del resultado del `DELETE`, no una consulta de existencia.
- **Consecuencia de DD-13/IN-03 registrada como decisión propia**: un dueño **con ficha y sin mascotas** también recibe **409**, porque `ficha_duenio.duenio_id` quedó en `NO ACTION`. No se borra la ficha antes para permitir la baja: eso sería inventar un borrado en cascada que la consigna no autoriza (IN-03: "No agregar `CASCADE` sin autorización"). Se documenta en el README como decisión propia y se cubre con un escenario de borde en la spec.
- **Alternativa descartada**: consultar si tiene mascotas antes de borrar. Viola la regla dura y reintroduce la carrera.

### 7. Alta de ficha: consultar solo el id del dueño, nunca la ficha (RN-03)

`crear_ficha` primero comprueba que el dueño exista consultando **solo su id**:

```python
resultado = await session.execute(select(Duenio.id).where(Duenio.id == duenio_id))
if resultado.scalar_one_or_none() is None:
    raise HTTPException(status_code=404, ...)
```

Después crea `FichaDuenio(duenio_id=..., telefono=..., direccion=...)` y hace `commit()`. Si el dueño ya tiene ficha, `UNIQUE (ficha_duenio.duenio_id)` produce `IntegrityError` → `rollback()` → 409.

- **Distinción explícita**: la consulta al dueño es la búsqueda del recurso de la ruta (necesaria para distinguir 404 de 409, Flujo 3). **No** se inspecciona `duenio.ficha` para decidir el conflicto: eso sería el `SELECT` previo de "¿ya existe la ficha?" que la regla dura prohíbe. El `UNIQUE` decide.
- **Por qué `select(Duenio.id)` y no `joinedload(Duenio.ficha)`**: para crear la ficha no hace falta cargar la ficha existente —solo saber si el dueño existe—, así que se trae una sola columna y se evita el `LEFT OUTER JOIN` y la materialización de la relación. La consulta sigue siendo una sentencia fija, sin carga perezosa, y no deja ninguna relación pendiente de cargar porque la respuesta usa solo la ficha recién creada.

**Alternativa descartada**: no consultar el dueño y dejar que la FK responda `IntegrityError`. No permite distinguir 404 (dueño inexistente) de 409 (ficha duplicada), que la tabla de endpoints exige por separado.

### 8. Mascotas del dueño: dos consultas fijas y lista simple (DD-10, DD-15)

`listar_mascotas_de_duenio` hace:

1. `select(Duenio.id).where(Duenio.id == duenio_id)` para distinguir 404 de lista vacía.
2. `select(Mascota).where(Mascota.duenio_id == duenio_id).order_by(Mascota.id)`.

Devuelve la lista tal cual y el router responde `list[MascotaResumenRead]`. Es un arreglo JSON simple, sin `items/total/page/size/pages`, porque la consigna solo exige paginación para `GET /mascotas/` (RN-13, DD-10). El orden por `id` ascendente es DD-15. No se carga `Mascota.duenio` ni `Mascota.turnos`: la vista resumida no los expone y cargarlos sería trabajo y consultas inútiles.

**Alternativa descartada**: `select(Duenio).options(selectinload(Duenio.mascotas))`. También son dos consultas, pero acopla la respuesta a la colección del ORM y hace más difícil ordenar y controlar el shape. Se prefiere la consulta explícita.

### 9. Códigos HTTP: quién produce cada uno (RN-12)

- **422**: lo produce FastAPI/Pydantic antes del handler — cuerpo inválido contra `DuenioCreate`, `DuenioUpdate` o `FichaCreate`, campos faltantes o de tipo incorrecto, y un `id` de ruta que no es entero (`GET /duenios/abc`), porque el parámetro se declara `int`.
- **404**: lo produce el service/router cuando el recurso de la ruta no existe. Nunca se devuelve 404 por un cuerpo inválido ni 422 por un recurso ausente.
- **409**: lo produce el service al capturar `IntegrityError` (email repetido, segunda ficha, baja con mascotas o con ficha). No se distingue por nombre de restricción para no acoplar el service al esquema; el mensaje propio indica el conflicto esperado en cada endpoint.
- **201** en las dos altas, **204** sin cuerpo en la baja, **200** en detalle, `PATCH` y listado de mascotas.

### 10. Router: prefijo, barra final y handlers asíncronos (SU-05, RN-17)

`APIRouter(prefix="/duenios", tags=["duenios"])` con `@router.post("/")` (ruta efectiva `/duenios/`, con barra final como la tabla de endpoints), `@router.get("/{duenio_id}")`, `@router.patch("/{duenio_id}")`, `@router.delete("/{duenio_id}", status_code=204)`, `@router.post("/{duenio_id}/ficha", status_code=201)` y `@router.get("/{duenio_id}/mascotas")`. Todos los handlers son `async def`, reciben la sesión con `Depends(get_session)` y delegan en el service; el router no contiene lógica de negocio (DD-02).

### 11. Imports del service: registrar los mappers, no usarlos

`app/modules/duenios/service.py` arranca con el mismo bloque de imports que `app/modules/practicas/service.py`:

```python
from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

import app.modules.duenios.models  # noqa: F401
import app.modules.mascotas.models  # noqa: F401

from app.modules.duenios.models import Duenio, FichaDuenio
from app.modules.duenios.schemas import (
    DuenioCreate,
    DuenioRead,
    DuenioUpdate,
    FichaCreate,
    FichaRead,
    MascotaResumenRead,
)
from app.modules.mascotas.models import Mascota
```

- **`import app.modules.mascotas.models  # noqa: F401`** es obligatorio: `Duenio.mascotas` es una relación declarada como string y el mapper de `Mascota` debe estar registrado antes de configurar `Duenio`; sin ese import, cualquier consulta sobre `Duenio` falla con `InvalidRequestError` ("expression 'Mascota' failed to locate a name"). Se necesita además para `select(Mascota)` del listado.
- `import app.modules.duenios.models  # noqa: F401` registra `Duenio` y `FichaDuenio` (necesario para `Duenio.ficha`).
- Los imports con `# noqa: F401` son **para registrar los mappers**, no para usar los nombres en el código: por eso llevan `noqa` (evitan el aviso de import sin uso) y por eso el mismo bloque importa nominalmente las clases que el service sí referencia (`Duenio`, `FichaDuenio`, `Mascota`). Si el service necesita otra relación registrada, se agrega el `import app.modules.<modulo>.models  # noqa: F401` correspondiente.

## Risks / Trade-offs

- [Riesgo] `session.delete()` del ORM anula las FK hijas (`UPDATE ... SET duenio_id = NULL`) y el rechazo llega por `NOT NULL` en lugar de por `RESTRICT`, con consultas extra. → Mitigación: se usa `delete()` de Core (decisión 6); el smoke verifica que el registro de sentencias muestra un solo `DELETE FROM duenio` y ningún `UPDATE`/`SELECT` de `mascota` ni de `ficha_duenio`.
- [Riesgo] Un `IntegrityError` sin `rollback()` deja la sesión inutilizable. → Mitigación: el `rollback()` está en el mismo `except`, antes de lanzar la excepción; el smoke encadena un 409 con una operación válida.
- [Riesgo] `IntegrityError` genérico traducido a 409 aunque la violación sea otra (por ejemplo `NOT NULL` al enviar `null` en el `PATCH`). → Mitigación: los casos normales solo pueden violar `UNIQUE` o las FK; responder 409 es conservador y coherente con "la base rechaza la escritura". Aceptado y documentado.
- [Riesgo] Serializar `Duenio.ficha` en el alta dispara carga perezosa y `MissingGreenlet`. → Mitigación: el alta construye `DuenioRead` con `ficha=None` (decisión 3); el smoke verifica que `POST /duenios/` responde 201 y no falla.
- [Trade-off] Un dueño con ficha y sin mascotas no se puede borrar por API (409 por `NO ACTION`). → Se acepta como consecuencia de DD-13/IN-03; la alternativa (borrar la ficha antes) inventaría una cascada no autorizada. Se documenta en el README y se cubre con un escenario de borde.
- [Trade-off] `GET /duenios/{id}/mascotas` hace dos consultas fijas (existencia del dueño + listado) en lugar de una. → Necesario para distinguir 404 de `[]`; el número es fijo y no crece con la cantidad de mascotas (RN-15).

## Plan de migración / rollback

- No hay migraciones (DD-01). El esquema ya existe (change [02]); este change solo agrega código.
- **Aplicación**: completar `schemas.py`, `service.py` y `router.py`; levantar `uvicorn app.main:app` con la base reiniciada (`python reiniciar.py`, change [09]) y ejecutar el smoke del change.
- **Rollback**: vaciar los tres archivos a stubs (`router = APIRouter()`). Sin impacto en la base ni en otros módulos: ningún módulo importa DTO de `duenios` y el router ya estaba registrado en `app/main.py` desde [01].

## UI Mockups

Decision: no (no UI)

Este change es exclusivamente backend: no agrega pantallas, componentes, estilos ni interacciones. No se crean mockups ni se aplica la compuerta visual.

## Preguntas abiertas

Ninguna que afecte este change. Los puntos que la consigna deja abiertos y tocan a `duenios` ya están resueltos como decisión propia: campos del `PATCH` (DD-08), ausencia de normalización del email (DD-09), forma de la lista de mascotas (DD-10), validaciones mínimas de la ficha y del email (DD-12) y regla de borrado de la ficha (DD-13/IN-03, con la consecuencia registrada en la decisión 6). Si la cátedra confirmara otra regla de borrado para `ficha_duenio`, el cambio se limita al `except` de la baja y a un escenario de la spec.
