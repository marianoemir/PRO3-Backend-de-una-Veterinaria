# Propuesta: practicas-catalogo

## Why

El change [02] `modelos-y-esquema` declaró la tabla `practica` (nombre `UNIQUE`, precio `NUMERIC(10,2)` con `CHECK precio > 0`) y la relación `Practica.turnos`, pero los archivos `schemas.py`, `service.py` y `router.py` del módulo `practicas` siguen siendo stubs vacíos. Sin este change **no existe la API del catálogo de prácticas**: no se puede dar de alta una práctica ni consultar el catálogo. Eso bloquea [06] `turnos-alta-transaccional` (que copia el precio del catálogo al reservar un turno, RN-06) y [10] `pruebas-http-y-evidencia` (casos C-02 y C-04). Este change materializa el **CRUD mínimo del catálogo** (alta + listado) con los códigos HTTP y las garantías que la consigna exige, sin tocar el modelo (propiedad de [02]).

## What Changes

- **`app/modules/practicas/schemas.py`**: se agregan dos DTO: `PracticaCreate` (sin `id`; `nombre` obligatorio; `precio` `Decimal` validado `> 0` en el DTO, RN-04) y `PracticaRead` (`id`, `nombre`, `precio` serializado como **string decimal**, DD-06).
- **`app/modules/practicas/service.py`**: `crear_practica(session, dto)` hace `INSERT` directo y, ante `IntegrityError` por nombre repetido, hace `rollback()` y propaga el conflicto (sin `SELECT` previo, DD-03); `listar_practicas(session)` hace un único `SELECT ... ORDER BY id` (DD-15).
- **`app/modules/practicas/router.py`**: `POST /practicas/` → **201** con `PracticaRead`, **409** si el nombre ya existe, **422** si `precio <= 0` o el cuerpo es inválido; `GET /practicas/` → **200** con el catálogo ordenado por `id`.
- **Sin** `PATCH`, sin `DELETE`, sin `GET /practicas/{id}`: la consigna no los lista (IN-02) y el catálogo se consume solo por alta y listado.

**BREAKING**: ninguno. Los archivos tocados son stubs vacíos del change [01]; no hay consumidores previos del módulo.

## Capabilities

### New Capabilities

- `practicas-catalogo`: alta y consulta del catálogo de prácticas veterinarias — validación de precio positivo en el DTO y en la base, detección de nombre repetido por la restricción `UNIQUE` (sin consulta previa) y listado ordenado por `id`, con dinero serializado como string decimal.

### Modified Capabilities

Ninguna. El modelo `Practica` ya existe (change [02]); este change solo agrega la capa de DTO, service y router sobre él.

## Impact

- **Código afectado**: `app/modules/practicas/schemas.py`, `app/modules/practicas/service.py`, `app/modules/practicas/router.py`. **No** se toca `app/modules/practicas/models.py` (propiedad de [02]).
- **Base de datos**: sin cambios de esquema; se reutilizan la tabla `practica`, su `UNIQUE (nombre)`, su `CHECK (precio > 0)` y su PK.
- **APIs**: aparecen `POST /practicas/` y `GET /practicas/` con los códigos 201/409/422 y 200 respectivamente.
- **Dependencias**: ninguna nueva (solo `fastapi`, `sqlmodel`, `sqlalchemy`, `pydantic` ya presentes). `app/main.py` ya registra el router de `practicas` (change [01]); no se edita.
- **Changes que desbloquea**: [06] `turnos-alta-transaccional` (copia `precio` del catálogo) y, a través de él, [10] `pruebas-http-y-evidencia`.
- **Riesgo principal**: serializar `Decimal` como string en `PracticaRead` (DD-06) y capturar `IntegrityError` con `rollback()` sin dejar la sesión en estado inválido (DD-03). Verificado por el smoke del change.