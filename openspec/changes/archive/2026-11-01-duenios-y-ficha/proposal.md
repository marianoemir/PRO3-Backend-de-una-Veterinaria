# Propuesta: duenios-y-ficha

## Why

El change [02] `modelos-y-esquema` declaró las tablas `duenio` (`email` `UNIQUE`) y `ficha_duenio` (`duenio_id` FK `UNIQUE`), con `Duenio.ficha` a uno (`uselist=False`) y `Duenio.mascotas` hacia `Mascota` con `ON DELETE RESTRICT`, pero `app/modules/duenios/{schemas,service,router}.py` siguen siendo stubs vacíos. Sin este change **no existe la API de dueños**: no se puede dar de alta un dueño, consultarlo con su ficha, corregirlo, darlo de baja, cargarle la ficha ni listar sus mascotas. Eso bloquea [05] `mascotas-y-paginacion` (necesita dueños creados por API para probar el alta de mascotas), [10] `pruebas-http-y-evidencia` (casos C-01, C-02, C-03 y C-05) y [11] `readme-y-entrega`. Este change materializa el **CRUD de dueños y la ficha uno a uno** con los códigos HTTP y las garantías que la consigna exige, sin tocar los modelos (propiedad de [02]).

## What Changes

- **`app/modules/duenios/schemas.py`**: se agregan los DTO `DuenioCreate` (`nombre` y `email`, **sin `id`**, RN-10), `DuenioUpdate` (`nombre` y `email` **opcionales**, DD-08), `DuenioRead` (`id`, `nombre`, `email` y `ficha` anidada o `null`), `FichaCreate` (`telefono` y `direccion` obligatorios, DD-12), `FichaRead` (`id`, `duenio_id`, `telefono`, `direccion`) y `MascotaResumenRead` (`id`, `nombre`, `especie`), una **vista resumida propia de este módulo** para `GET /duenios/{id}/mascotas`; `duenios/schemas.py` **no importa** DTO de `mascotas` ni de ningún otro módulo.
- **`app/modules/duenios/service.py`**: `crear_duenio` (INSERT directo; `IntegrityError` por `UNIQUE(email)` → `rollback()` → 409, **sin `SELECT` previo**, DD-03), `obtener_duenio` (una consulta con `joinedload(Duenio.ficha)`, RN-14/RN-15), `actualizar_duenio` (aplica solo lo enviado con `exclude_unset`, RN-11; email que colisiona → `rollback()` → 409), `borrar_duenio` (`DELETE` que deja decidir a la base: `RESTRICT` de `mascota` → `rollback()` → 409, RN-08), `crear_ficha` (dueño inexistente → 404; `UNIQUE(duenio_id)` → `rollback()` → 409, RN-03) y `listar_mascotas_de_duenio` (dueño inexistente → 404; lista simple, DD-10).
- **`app/modules/duenios/router.py`**: `POST /duenios/` → **201**, **409**, **422**; `GET /duenios/{id}` → **200** con ficha, **404**, **422** si el id no es entero; `PATCH /duenios/{id}` → **200**, **404**, **409**, **422**; `DELETE /duenios/{id}` → **204**, **404**, **409**; `POST /duenios/{id}/ficha` → **201**, **404**, **409**; `GET /duenios/{id}/mascotas` → **200** con lista simple (`[]` si no tiene), **404**. Todos los handlers `async def` (RN-17).
- **Fuera de alcance (explícito)**:
  - **No** se implementa `GET /duenios/` (listado de dueños): la tabla de endpoints no lo lista (IN-01).
  - **No** se implementa `DELETE` de ficha ni `PATCH` de ficha: la tabla de endpoints no los lista (IN-02).
  - **No** se implementa `DELETE /mascotas/{id}` ni paginación en `GET /duenios/{id}/mascotas` (DD-10).
  - **No** se tocan `app/modules/duenios/models.py` ni `app/modules/mascotas/models.py` (propiedad de [02]), `app/main.py`, `reiniciar.py`, `test/**`, `README.md` ni `CHANGES.md`.
  - **No** se agregan migraciones (Alembic), autenticación, repositorios ni colas.

**BREAKING**: ninguno. Los archivos tocados son stubs vacíos del change [01]; ningún módulo consume todavía el módulo `duenios` y ningún DTO se comparte entre módulos.

## Capabilities

### New Capabilities

- `duenios-y-ficha`: gestión del padrón de dueños y de su ficha uno a uno — alta con email único garantizado por la base, detalle con la ficha precargada, `PATCH` parcial de los campos enviados, baja bloqueada mientras existan mascotas o ficha, alta de una única ficha por dueño y consulta de las mascotas del dueño como lista simple, todo con códigos HTTP explícitos (201/204/200/404/409/422) y sin consultas previas de existencia.

### Modified Capabilities

Ninguna. El esquema `duenio`/`ficha_duenio` ya existe y está especificado en `modelo-de-datos` (change [02]); este change solo agrega la capa de DTO, service y router sobre él y no cambia ningún requisito de esa capacidad.

## Impact

- **Código afectado**: `app/modules/duenios/schemas.py`, `app/modules/duenios/service.py`, `app/modules/duenios/router.py`. **No** se toca `models.py` (propiedad de [02]), ni `app/main.py` (ya registra el router de `duenios`, change [01]).
- **Base de datos**: sin cambios de esquema; se reutilizan `UNIQUE (duenio.email)`, `UNIQUE (ficha_duenio.duenio_id)`, la FK `mascota.duenio_id ON DELETE RESTRICT` y la FK `ficha_duenio.duenio_id` sin `ON DELETE` (`NO ACTION`, DD-13).
- **APIs**: aparecen los seis endpoints del módulo con los códigos de la tabla de `knowledge-base/02_descripcion_general.md`; no se agrega ninguno que no esté listado.
- **Reglas de negocio cubiertas**: RN-01 (email único), RN-03 (una ficha por dueño), RN-08 (no borrar dueño con mascotas), RN-10 (DTO separados, alta sin `id`), RN-11 (`PATCH` con `exclude_unset`), RN-12 (códigos 201/204/404/409/422), RN-14/RN-15/RN-16 (carga anticipada y número fijo de consultas), RN-17 (handlers `async def`), RN-21 (sesión por petición).
- **Dependencias**: ninguna nueva (solo `fastapi`, `sqlmodel`, `sqlalchemy`, `pydantic` ya presentes). `app/core/database.py` ya expone `get_session`.
- **Changes que desbloquea**: [05] `mascotas-y-paginacion` (necesita dueños por API), [10] `pruebas-http-y-evidencia` (C-01, C-02, C-03, C-05) y, a través de ellos, [11] `readme-y-entrega`.
- **Riesgo principal**: que el `DELETE` del ORM anule las FK hijas en lugar de dejar actuar al `RESTRICT`/`NO ACTION` de la base (se resuelve con un `DELETE` de Core, justificado en `design.md`), y que un `IntegrityError` sin `rollback()` deje la sesión inutilizable. Ambos se verifican en el smoke del change.
