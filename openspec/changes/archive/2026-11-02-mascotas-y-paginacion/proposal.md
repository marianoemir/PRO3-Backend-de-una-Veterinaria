# Propuesta: mascotas-y-paginacion

## Why

Los changes [02] `modelos-y-esquema` y [03] `duenios-y-ficha` ya dejaron el modelo `Mascota` (`id`, `nombre`, `especie`, `duenio_id` FK `ON DELETE RESTRICT` con índice) y el padrón de dueños operable por API, pero `app/modules/mascotas/{schemas,service,router}.py` siguen siendo stubs vacíos. Sin este change **no existe la API de mascotas**: no se puede registrar una mascota a nombre de un dueño, consultarla con su dueño ni recorrer el padrón paginado. Eso bloquea el caso **C-04** de [10] `pruebas-http-y-evidencia` (mascota con dueño inexistente → 409) y, a través de él, [11] `readme-y-entrega`. Este change materializa el **alta, el detalle y el listado paginado de mascotas** con los códigos HTTP y las garantías que la consigna exige, sin tocar los modelos (propiedad de [02]) ni el módulo `duenios` (propiedad de [03]).

## What Changes

- **`app/modules/mascotas/schemas.py`**: se agregan los DTO `MascotaCreate` (`nombre`, `especie` y `duenio_id`; **sin `id`**, RN-10; `especie` texto libre no vacío, DD-12), `DuenioResumenRead` (`id`, `nombre`), una **vista resumida propia de este módulo** para no importar DTO de `duenios` (RN-10 y regla de CHANGES.md), `MascotaRead` (`id`, `nombre`, `especie` y el dueño resumido) y `PaginaMascotasRead` con el envoltorio exacto `{ items, total, page, size, pages }` (RN-13).
- **`app/modules/mascotas/service.py`**: `crear_mascota` (INSERT directo; si el `duenio_id` no existe la FK lo rechaza → `IntegrityError` → `rollback()` → 409, **sin `SELECT` previo**, DD-03) y `listar_mascotas` (`count(*)` + página con `offset`/`limit` y `joinedload(Mascota.duenio)`, orden por `id`, **dos consultas fijas**, RN-13/RN-15/DD-15) más `obtener_mascota` (una consulta con carga anticipada del dueño; `None` → 404, RN-14).
- **`app/modules/mascotas/router.py`**: `POST /mascotas/` → **201**, **409**, **422**; `GET /mascotas/?page=&size=` → **200**, **422** (`size` fuera de 1..100, `page` no válida o más allá de `pages`); `GET /mascotas/{id}` → **200** con su dueño, **404**. Todos los handlers `async def` (RN-17) y con `Depends(get_session)` (RN-21).
- **Fuera de alcance (explícito)**:
  - **No** se implementa `DELETE /mascotas/{id}`: no está en la tabla de endpoints (IN-02, regla dura 10 de `AGENTS.md`).
  - **No** se implementa `GET /mascotas/?duenio_id=` ni ningún listado de mascotas por dueño: ese listado ya existe como `GET /duenios/{id}/mascotas` en el change [03] (DD-10).
  - **No** se implementa `PATCH /mascotas/{id}`, ni búsqueda, ni filtros, ni orden configurable: la consigna no los enuncia.
  - **No** se tocan `app/modules/mascotas/models.py` (propiedad de [02]), `app/modules/duenios/*` (propiedad de [03]), `app/main.py` (ya registra el router de `mascotas`, change [01]), `reiniciar.py`, `test/**`, `README.md` ni `CHANGES.md`.
  - **No** se agregan migraciones (Alembic), autenticación, repositorios ni colas.

**BREAKING**: ninguno. Los tres archivos tocados son stubs vacíos del change [01]; ningún módulo importa DTO de `mascotas` y el router ya estaba registrado en `app/main.py`.

## Capabilities

### New Capabilities

- `mascotas-y-paginacion`: alta de mascotas con el dueño validado por la clave foránea de la base (409 sin consulta previa de existencia), detalle con el dueño precargado en una sola consulta y listado paginado con el envoltorio `{ items, total, page, size, pages }`, `size` acotado a 1..100, página fuera de `pages` → 422, primera página siempre 200 y un número fijo de consultas, todo con los códigos HTTP de la tabla de endpoints.

### Modified Capabilities

Ninguna. `modelo-de-datos` describe el esquema `mascota`, que ya existe y no cambia: este change no agrega columnas, restricciones ni índices. `duenios-y-ficha` ya cubre `GET /duenios/{id}/mascotas` con su propia vista resumida de mascota; este change no modifica ese requisito ni importa sus DTO, solo agrega los tres endpoints de `mascotas` que la tabla de `knowledge-base/02_descripcion_general.md` asigna a otro módulo.

## Impact

- **Código afectado**: `app/modules/mascotas/schemas.py`, `app/modules/mascotas/service.py`, `app/modules/mascotas/router.py`. **No** se toca `models.py` (propiedad de [02]) ni `app/main.py` (ya registra el router, change [01]).
- **Base de datos**: sin cambios de esquema; se reutilizan la FK `mascota.duenio_id ON DELETE RESTRICT` con su índice y la PK autoincremental de `mascota`.
- **APIs**: aparecen los tres endpoints de `mascotas` con los códigos de la tabla de `knowledge-base/02_descripcion_general.md`; no se agrega ninguno que no esté listado.
- **Reglas de negocio cubiertas**: RN-10 (DTO separados de los modelos de tabla y alta sin `id`), RN-12 (201/404/409/422), RN-13 (envoltorio de paginación, `size` 20 por defecto y 1..100, página fuera de `pages` → 422, primera página siempre responde), RN-14/RN-15/RN-16 (carga anticipada y número fijo de consultas), RN-17 (handlers `async def`), RN-21 (sesión por petición). Se apoya en las decisiones DD-03 (garantizar en la base, no preguntar antes), DD-04 (carga anticipada explícita), DD-12 (`especie` texto libre no vacío) y DD-15 (`page`/`size` como query params y orden por `id`).
- **Dependencias**: ninguna nueva (solo `fastapi`, `sqlmodel`, `sqlalchemy`, `pydantic` ya presentes). `app/core/database.py` ya expone `get_session`.
- **Changes que desbloquea**: [10] `pruebas-http-y-evidencia` (caso C-04 y el listado paginado) y, a través de él, [11] `readme-y-entrega`.
- **Riesgo principal**: que la respuesta del alta dependa de una carga perezosa de `Mascota.duenio` y falle con `MissingGreenlet` (se resuelve con una lectura explícita con `joinedload` después del `INSERT`, justificada en `design.md`), y que la validación de página fuera de rango se implemente con una consulta extra o rompa el caso de la base vacía (se resuelve con el `count(*)` ya necesario y la excepción de la primera página, verificado en el smoke).
